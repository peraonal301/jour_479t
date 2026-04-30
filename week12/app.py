# load libraries

from flask import Flask, jsonify, request
import pandas as pd
import os

# start app
app = Flask(__name__)

# load the power outages data once when the app starts
outages_data = pd.read_csv('week12/data/Power_Outages_-_County_20260430.csv')

# clean the data: remove commas from customers column and convert to int
outages_data['customers'] = outages_data['customers'].str.replace(',', '').astype(int)

# defining a function that converts a dataframe into a list of JSON dictionaries
def rows_to_json(df):
    """Convert a DataFrame to a list of dicts, handling NaN values."""
    return df.where(pd.notna(df), None).to_dict(orient='records')

""" 
Below is the information for the root directory.
When we go to the root directory '/' there will be a landing page with all of the available endpoints as JSON.
Reminder that you have to run python week12/app.py in the terminal and ensure the app is running before you can actually access this endpoint.  
"""
@app.route('/') # defines the URL endpoint: /
def index():
    return jsonify({
        # we can customize what is shown on this page. It will be shown as JSON, but
        # other API endpoints for landing pages might have fancier built-out pages to show information
        'description': 'Power Outages API',
        'endpoints': [
            {
                'path': '/api/outages', # this links to /api/outages
                'method': 'GET',
                'description': 'Return all outages data',
                'params': ['area', 'min_outages', 'max_outages']
            },
            {
                'path': '/api/outages/search',
                'method': 'GET',
                'description': 'Search by county area name with optional outage filters.',
                'params': ['area (required)', 'min_outages', 'max_outages']
            },
            {
                'path': '/api/outages/worst',
                'method': 'GET',
                'description': 'List counties with highest number of outages with optional customer filtering.',
                'params': ['n (default: 10)', 'min_customers', 'max_customers']
            },
            {
                'path': '/api/outages/affected',
                'method': 'GET',
                'description': 'List counties with most customers affected by outages.',
                'params': ['n (default: 10)']
            },
        ]
    })

"""
Endpoint 1: GET /api/outages

Returns all outages records. 
Supports optional query parameters

Examples of parameters:
  ?area=Baltimore
  ?min_outages=10
  ?max_outages=100
"""
@app.route('/api/outages') # defines the URL endpoint: /api/outages
def get_outages(): # function that runs when this endpoint is accessed
    # create a dataframe that is a copy of our outages_data dataframe, so we don't modify the original
    df = outages_data.copy() 

    ## This is where we define our parameters

    # get the value of ?area= from the URL (returns None if not provided)
    area = request.args.get('area')
    # get the value of ?min_outages= and convert it to an integer (number)
    min_outages = request.args.get('min_outages', type=int)
    # get the value of ?max_outages= and convert it to an integer
    max_outages = request.args.get('max_outages', type=int)

    # if an area was provided in the URL
    if area:
        # filter the dataframe to only include rows where area matches.
        # case=False makes the comparison case-insensitive
        df = df[df['area'].str.contains(area, case=False, na=False)]
    # if a minimum outages was provided,
    if min_outages is not None:
        # filter to only rows where outages is greater than or equal to min_outages.
        df = df[df['outages'] >= min_outages]
    # if a maximum outages was provided,
    if max_outages is not None:
        # filter to only rows where outages is less than or equal to max_outages.
        df = df[df['outages'] <= max_outages]
    
    # return the result after this filtering
    return jsonify({
        # return the total number of rows after filtering
        'count': len(df),
        # convert dataframe to JSON format using the rows_to_json() function we defined earlier.
        'results': rows_to_json(df)
    })


"""
Endpoint 2: GET /api/outages/search?area=

Area parameter is required. 
Example: GET /api/outages/search?area=Baltimore&min_outages=5&max_outages=50

Case-insensitive partial-match search on the "area" column with optional outage filters

"""
@app.route('/api/outages/search') # defines the endpoint: /api/outages/search
def search_outages():  # function that runs when this endpoint is accessed
    
    ### Defining our parameters
    # get the value of ?area= from the URL
    # if no area is provided, default to an empty string ''
    area = request.args.get('area', '')
    # get the value of ?min_outages= and convert it to an integer
    min_outages = request.args.get('min_outages', type=int)
    # get the value of ?max_outages= and convert it to an integer
    max_outages = request.args.get('max_outages', type=int)
    
    # if the user did NOT provide an area parameter,
    if not area:
        # return an error message as JSON
        # 400 error means the client made a mistake
        ### This makes our area parameter required
        return jsonify({'error': 'Provide a ?area= query parameter'}), 400

     # create a filtered dataframe that looks at 'area' to see if it contains 
     # the string that the user specified in ?area= in the URL
     # case=False makes it case-insensitive
     # na=False prevents errors if there are missing values
    df = outages_data[outages_data['area'].str.contains(area, case=False, na=False)]
    
    # apply additional filters
    # if a minimum outages was provided,
    if min_outages is not None:
        # filter to only rows where outages is greater than or equal to min_outages
        df = df[df['outages'] >= min_outages]
    # if a maximum outages was provided,
    if max_outages is not None:
        # filter to only rows where outages is less than or equal to max_outages
        df = df[df['outages'] <= max_outages]
    
    # return results as JSON
    return jsonify({
        # return count of total rows 
        'count': len(df),
        # return the data as JSON
        'results': rows_to_json(df)
    })

"""
Endpoint 3: GET /api/outages/worst?n=10

Returns the top N counties with highest number of outages. Default N is 10.
Optional parameters to filter by customer count.
Example: GET /api/outages/worst?n=5&min_customers=50000&max_customers=300000
"""
@app.route('/api/outages/worst')
def worst_outages():
    ### Defining our parameters
    # if there is something after ?n=, save it to the object n.
    # if there is nothing after ?n=, default to 10
    # ensure n is an integer
    n = request.args.get('n', default=10, type=int)
    # get the value of ?min_customers= and convert it to an integer
    min_customers = request.args.get('min_customers', type=int)
    # get the value of ?max_customers= and convert it to an integer
    max_customers = request.args.get('max_customers', type=int)
    
    # filter our outages data to the largest N outages
    df = outages_data.nlargest(n, 'outages')
    
    # apply additional customer filters
    # if a minimum customers was provided,
    if min_customers is not None:
        # filter to only rows where customers is greater than or equal to min_customers
        df = df[df['customers'] >= min_customers]
    # if a maximum customers was provided,
    if max_customers is not None:
        # filter to only rows where customers is less than or equal to max_customers
        df = df[df['customers'] <= max_customers]
    
    # return as JSON
    return jsonify({
        'count': len(df), # give the count of rows
        'results': rows_to_json(df) # turn rows to json
    })


"""
Endpoint 4: GET /api/outages/affected?n=10

Returns the top N counties with most customers affected by outages. Default N is 10.
"""
@app.route('/api/outages/affected')
def most_affected():
    ### Defining our parameter n
    # if there is something after ?n=, save it to the object n.
    # if there is nothing after ?n=, default to 10
    # ensure n is an integer
    n = request.args.get('n', default=10, type=int)
    # filter our outages data to the largest N by customers affected
    df = outages_data.nlargest(n, 'customers')
    
    # return as JSON
    return jsonify({
        'count': len(df), # give the count of rows (this should be same as N)
        'results': rows_to_json(df) # turn rows to json
    })


if __name__ == '__main__':
    # debug=True gives you auto-reload when you save the file
    # port=5000 tells Flask which port to run the server on
    # so you can access it at http://127.0.0.1:5000/
    app.run(debug=True, port=5000)
