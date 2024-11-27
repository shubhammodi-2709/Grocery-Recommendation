import pandas as pd
import sqlite3
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder
import numpy as np

# Function to load orders data from the database
def load_data(db_name):
    conn = sqlite3.connect(db_name)
    orders = pd.read_sql_query('SELECT * FROM orders', conn)
    conn.close()
    return orders

# Function to load product data from the database
def load_products(db_name):
    conn = sqlite3.connect(db_name)
    products = pd.read_sql_query('SELECT * FROM Products', conn)
    conn.close()
    return products

# Preprocessing orders into a basket format
def preprocess_orders(orders):
    basket = (orders.groupby(['user_id', 'product_id'])['quantity']
                   .sum().unstack().reset_index().fillna(0)
                   .set_index('user_id'))
    basket = basket.applymap(lambda x: 1 if x > 0 else 0)  # Convert quantities to binary
    return basket

# Generate association rules from orders
def generate_recommendations(orders, min_support=0.01, min_confidence=0.5):
    basket = preprocess_orders(orders)
    frequent_itemsets = apriori(basket, min_support=min_support, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    return rules

# Generate content-based recommendations based on product attributes
def generate_content_based_recommendations(products, user_orders):
    # Assuming products have attributes for generating content-based recommendations
    encoder = OneHotEncoder()
    # Exclude 'ID' and 'ProductName' columns for feature encoding
    product_features = encoder.fit_transform(products.drop(columns=['ID', 'ProductName'])).toarray()

    # Calculate cosine similarity between all products
    similarity_matrix = cosine_similarity(product_features)

    purchased_ids = user_orders['product_id'].unique()
    recommended_indices = []
    for product_id in purchased_ids:
        product_idx = products[products['ID'] == product_id].index[0]
        # Get the indices of the most similar products (top 3 excluding the product itself)
        similar_indices = np.argsort(similarity_matrix[product_idx])[::-1][1:4]  # Top 3 similar
        recommended_indices.extend(similar_indices)

    recommended_ids = products.iloc[recommended_indices]['ID'].unique()
    return products[products['ID'].isin(recommended_ids)]

# Combine association rule-based and content-based recommendations
def recommend_products(db_name, user_id):
    orders = load_data(db_name)  # Load order data
    products = load_products(db_name)  # Load product data

    rules = generate_recommendations(orders)  # Generate association rules
    rule_based_recommendations = set()

    if not rules.empty:
        for index, row in rules.iterrows():
            if user_id in row['antecedents']:  # Check if the user has bought the antecedent products
                rule_based_recommendations.update(row['consequents'])

    # Get the orders of the user
    user_orders = orders[orders['user_id'] == user_id]
    content_based_recommendations = generate_content_based_recommendations(products, user_orders)

    # Combine the recommendations (both rule-based and content-based)
    combined_recommendations = set(rule_based_recommendations) | set(content_based_recommendations['ID'].tolist())

    # Return products that are recommended (both rule-based and content-based)
    return products[products['ID'].isin(combined_recommendations)].to_dict('records')
