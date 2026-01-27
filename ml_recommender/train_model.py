import recommender as rec
import pandas as pd

# Use these first run to prep data and serialize it
dataset = rec.prepare_dataset()
dataset.to_pickle("dataset.pkl")

# Use this line after serializing data so you don't have to redo prep work everytime you train
dataset = pd.read_pickle("dataset.pkl")

model = rec.train_model(dataset)
model.save_model("dota_item_recommender_model_statless.txt")