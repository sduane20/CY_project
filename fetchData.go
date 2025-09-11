package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time" // Import the time package for date handling
)

const (
	url        = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/Louisville_Metro_KY_Property_Foreclosures/FeatureServer/0/query"
	batchSize  = 1000
	outputDir  = "data"
	outputFile = "Louisville_Metro_KY_-_Property_Foreclosures.csv" // Renamed for clarity
	workers    = 5
	maxBatches = 300 // safety limit → 300 * 1000 = 300k rows max
)

// --- DEFINED HEADERS FOR CSV ORDERING ---
// This slice ensures the output CSV has the exact column order you need.
var csvHeaders = []string{
	"House_Nr", "Dir", "Street_Name", "St_Type", "Post_Dir", "Zip", "L_S", "CD",
	"Neighborhood", "Full_Parcel_ID", "Census_Tract", "Action_Filed", "Case_",
	"Case_Style", "Sale_Date", "Sale_Price", "Purchaser", "ObjectId",
}

type Feature struct {
	Attributes map[string]interface{} `json:"attributes"`
}

type QueryResult struct {
	Features []Feature `json:"features"`
}

// formatValue handles converting API data into the correct CSV string format.
// It specifically processes nil values and date timestamps.
func formatValue(key string, value interface{}) string {
	// 1. Handle nil values first, which appear as <nil>
	if value == nil {
		return ""
	}

	// 2. Check if the key corresponds to a date field
	if key == "Action_Filed" || key == "Sale_Date" {
		// The API returns timestamps as float64 (milliseconds)
		if timestamp, ok := value.(float64); ok {
			if timestamp == 0 {
				return ""
			}
			// Convert milliseconds to seconds
			sec := int64(timestamp / 1000)
			// Create a time.Time object in UTC
			t := time.Unix(sec, 0).UTC()
			// Format to the desired layout: YYYY/MM/DD HH:MM:SS+00
			return t.Format("2006/01/02 15:04:05+00")
		}
	}

	// 3. For all other types, convert to a string
	// Also handles the edge case where a value might literally be "<nil>"
	s := fmt.Sprintf("%v", value)
	if s == "<nil>" {
		return ""
	}
	return s
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

	// fmt.Println("Requesting:", req.URL.String()) // Uncomment for debugging

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

	fmt.Println("Starting data fetch...")

	// Worker goroutines
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for offset := range offsets {
				records, err := fetchBatch(offset, client)
				if err != nil {
					fmt.Printf("Error fetching offset %d: %v\n", offset, err)
					continue
				}

				if len(records) == 0 {
					// This can happen normally when we reach the end of the data.
					// To stop fetching once we hit an empty batch, you could add logic here
					// to close the 'offsets' channel, but for a fixed maxBatches, this is fine.
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

	fmt.Printf("Fetched %d total records.\n", len(allData))

	// Save to CSV
	if len(allData) > 0 {
		if err := os.MkdirAll(outputDir, os.ModePerm); err != nil {
			panic(err)
		}

		filePath := outputDir + "/" + outputFile
		file, err := os.Create(filePath)
		if err != nil {
			panic(err)
		}
		defer file.Close()

		writer := csv.NewWriter(file)
		defer writer.Flush()

		// --- MODIFIED CSV WRITING LOGIC ---

		// 1. Write headers using the predefined ordered slice
		if err := writer.Write(csvHeaders); err != nil {
			panic(err)
		}

		// 2. Write rows, ensuring values are in the correct order
		for _, record := range allData {
			row := make([]string, len(csvHeaders))
			for i, key := range csvHeaders {
				// Get value from map and format it using our new helper function
				row[i] = formatValue(key, record[key])
			}
			if err := writer.Write(row); err != nil {
				// Log error but continue trying to write other rows
				fmt.Printf("Error writing record to CSV: %v\n", err)
			}
		}

		fmt.Println("✅ Data saved to", filePath)
	} else {
		fmt.Println("⚠️ No data was retrieved from the API.")
	}
}
