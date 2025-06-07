import csv

def convert_csv_to_js():
    # Read the CSV file
    with open('data/tle_data.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row if exists
        
        # Create a list to store all values
        data = []
        
        # Read each row and append values to the list
        for row in csv_reader:
            if len(row) >= 3:  # Ensure we have all three columns
                data.extend([row[0], row[1], row[2]])
    
    # Create the JavaScript file
    with open('satellite-tracker/data/tle_data.js', 'w') as js_file:
        # Write the data array
        js_file.write('const data = [\n')
        # Write each value with proper formatting
        for i, value in enumerate(data):
            js_file.write(f'    "{value}"')
            if i < len(data) - 1:  # Add comma for all but last item
                js_file.write(',')
            js_file.write('\n')
        js_file.write('];\n\n')
        js_file.write('export default data;')

if __name__ == '__main__':
    convert_csv_to_js()
    print("Conversion completed successfully!") 