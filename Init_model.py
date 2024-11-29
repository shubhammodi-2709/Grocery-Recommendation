import pandas as pd
from sklearn.cluster import KMeans, MiniBatchKMeans
import numpy as np
import os
import joblib

class ProductRecommender:
    def __init__(self, data_path, model_path, n_clusters=5):
        """
        Initialize the recommender system.

        Args:
            data_path (str): Path to the CSV file containing product data.
            model_path (str): Path to save/load the model.
            n_clusters (int): Number of clusters for k-means.
        """
        self.data_path = data_path
        self.model_path = model_path
        self.n_clusters = n_clusters
        self.model = None
        self.data = None
        
        # Load existing model and data if available
        self._load_model_and_data()

    def _load_model_and_data(self):
        """Load the model and data if they exist."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        if os.path.exists(self.data_path):
            self.data = pd.read_csv(self.data_path)
        else:
            self.data = pd.DataFrame(columns=['ID', 'SameID', 'Price'])

    def train_model(self):
        """Train the k-means model on the current dataset."""
        if self.data.empty:
            raise ValueError("No data available to train the model.")
        
        # Train the k-means model
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42)
        self.data['Cluster'] = self.model.fit_predict(self.data[['SameID', 'Price']])
        
        # Save the model
        joblib.dump(self.model, self.model_path)

    def add_new_order(self, product_id, same_id, price):
        """
        Add a new order to the dataset and update the model.

        Args:
            product_id (int): ID of the new product.
            same_id (int): SameID category of the product.
            price (float): Price of the product.
        """
        # Add the new product to the dataset
        new_entry = {'ID': product_id, 'SameID': same_id, 'Price': price}
        self.data = pd.concat([self.data, pd.DataFrame([new_entry])], ignore_index=True)
        
        # Save the updated dataset
        self.data.to_csv(self.data_path, index=False)
        
        # Retrain or incrementally update the model
        self.train_model()

    def recommend_products(self, product_id):
        """
        Recommend products based on the cluster of the given product.

        Args:
            product_id (int): The ID of the product for which recommendations are needed.

        Returns:
            list: Recommended products (excluding the input product).
        """
        if self.model is None:
            raise ValueError("The model has not been trained yet. Train the model first.")
        
        # Ensure the 'Cluster' column exists
        if 'Cluster' not in self.data.columns:
            raise ValueError("Cluster information is missing. Train the model to assign clusters.")
        
        if product_id not in self.data['ID'].values:
            return f"Product ID {product_id} not found in the dataset."
        
        # Get the cluster of the given product
        product_cluster = self.data.loc[self.data['ID'] == product_id, 'Cluster'].values[0]
        
        # Find products in the same cluster (excluding the input product)
        recommendations = self.data[(self.data['Cluster'] == product_cluster) & (self.data['ID'] != product_id)]
        return recommendations[['ID', 'SameID', 'Price']].to_dict('records')