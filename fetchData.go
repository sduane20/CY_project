package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"sync"
)

const (
	url        = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/Louisville_Metro_KY_Property_Foreclosures/FeatureServer/0/query"
	batchSize  = 1000
	outputDir  = "data"
	outputFile = "data.csv"
	workers    = 5
	maxBatches = 300 // safety limit → 100 * 1000 = 100k rows max
)

type Feature struct {
	Attributes map[string]interface{} `json:"attributes"`
}

type QueryResult struct {
	Features []Feature `json:"features"`
}

func fetchBatch(offset int, client *http.Client) ([]map[string]interface{}, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("where", "1=1")
	q.Add("outFields", "*")
	q.Add("returnGeometry", "false")
	q.Add("f", "json")
	q.Add("resultOffset", strconv.Itoa(offset))
	q.Add("resultRecordCount", strconv.Itoa(batchSize))
	req.URL.RawQuery = q.Encode()

	fmt.Println("Requesting:", req.URL.String())

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("status code %d", resp.StatusCode)
	}

	var result QueryResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	records := make([]map[string]interface{}, 0, len(result.Features))
	for _, feature := range result.Features {
		records = append(records, feature.Attributes)
	}

	return records, nil
}

func main() {
	client := &http.Client{}

	var allData []map[string]interface{}
	var mu sync.Mutex

	offsets := make(chan int, workers)
	var wg sync.WaitGroup

	// Worker goroutines
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for offset := range offsets {
				records, err := fetchBatch(offset, client)
				if err != nil {
					fmt.Println("Error fetching offset", offset, ":", err)
					continue
				}

				if len(records) == 0 {
					continue
				}

				mu.Lock()
				allData = append(allData, records...)
				mu.Unlock()
			}
		}()
	}

	// Feed offsets up to maxBatches
	for i := 0; i < maxBatches; i++ {
		offsets <- i * batchSize
	}
	close(offsets)

	// Wait for workers to finish
	wg.Wait()

	// Save to CSV
	if len(allData) > 0 {
		if err := os.MkdirAll(outputDir, os.ModePerm); err != nil {
			panic(err)
		}

		file, err := os.Create(outputDir + "/" + outputFile)
		if err != nil {
			panic(err)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		// Write headers
		headers := []string{}
		for key := range allData[0] {
			headers = append(headers, key)
		}
		writer.Write(headers)

		// Write rows
		for _, record := range allData {
			row := []string{}
			for _, key := range headers {
				if val, ok := record[key]; ok {
					row = append(row, fmt.Sprintf("%v", val))
				} else {
					row = append(row, "")
				}
			}
			writer.Write(row)
		}

		fmt.Println("✅ Data saved to", outputDir+"/"+outputFile)
	} else {
		fmt.Println("⚠️ No data retrieved.")
	}
}
