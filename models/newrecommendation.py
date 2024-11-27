import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load the dataset
data_path = 'GroceryProducts.csv'
grocery_data = pd.read_csv(data_path)

# Preprocess the data for clustering
features = grocery_data[['Price']].values  # Using 'Price' for simplicity; add more features as needed

# Step 1: Clustering using K-Means
num_clusters = 5  # Define number of clusters
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
grocery_data['Cluster'] = kmeans.fit_predict(features)

# Step 2: Compute similarity for content-based filtering
# Using 'Type' as an example for content similarity
product_types = grocery_data['Type'].values.reshape(-1, 1)
similarity_matrix = cosine_similarity(product_types, product_types)

# Step 3: Hybrid Recommendation Function
def recommend_products(product_id, num_recommendations=5):
    # Find the cluster of the given product
    product_cluster = grocery_data.loc[grocery_data['ID'] == product_id, 'Cluster'].values[0]

    # Get all products in the same cluster
    cluster_products = grocery_data[grocery_data['Cluster'] == product_cluster]

    # Compute similarity scores within the cluster
    product_index = grocery_data[grocery_data['ID'] == product_id].index[0]
    cluster_indices = cluster_products.index
    cluster_similarity = similarity_matrix[product_index, cluster_indices]

    # Rank products by similarity
    ranked_products = cluster_products.copy()
    ranked_products['Similarity'] = cluster_similarity
    ranked_products = ranked_products.sort_values(by='Similarity', ascending=False)

    # Return top N recommendations
    recommendations = ranked_products.head(num_recommendations)
    return recommendations[['ProductName', 'Price', 'Similarity']]

# Example usage
product_id_to_test = 4  # Replace with a valid ID from your dataset
recommendations = recommend_products(product_id_to_test)
print("Recommendations:")
print(recommendations)
