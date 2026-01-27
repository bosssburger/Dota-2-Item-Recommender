# Dota 2 Item Recommender

## About the Project

This project is an AI and ML powered item recommender for the popular MOBA game Dota 2. In Dota, players choose heroes to play during a match. Throughout the game, players will earn gold by doing different tasks such as farming creeps or getting kills on enemy heroes. They use gold to purchase items which can alter the gameplay of their hero, give them stats to make their hero stronger, or obtain powerful new active abilities. With a wide variety of items, the best item to build in a given match often depends on the hero the player chooses as well as the capabilities of the heroes on the enemy team. Choosing the correct items to build is a large component of doing well in the game.

I created this project because I just started playing Dota 2 and while there are some existing resources for choosing items to build such as DotaBuff and player guides, I found each of these to have similar issues. Dotabuff, while excellent for statistics, provides only items listed by their pick rate with no context on the matches they were built in. Player guides can provide slightly more context but often assume that the reader has a baseline knowledge of all the Dota 2 heroes and item choices which I do not have. I thought that it would be great if I could have an experienced player explaining to me why certain items are chosen in certain situations, but none of my friends play Dota so I did the next best thing and got an AI to explain it to me. The project started as an idea of feeding a LLM some items and asking it why they were good. I then decided to expand the project to include a ML model because I thought it would be something interesting to try. As a result I also needed to program a data collector to have enough training information for the model.

## Built With

- LightGBM
- Google Gemini 3
- OpenDota

## Getting Started

### Prerequisites

- pip

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/bosssburger/Dota-2-Item-Recommender.git
   ```
2. Install packages from requirements.txt
   ```sh
   pip install -r requirements.txt
   ```
3. Get an OpenDota API Key from [https://www.opendota.com/api-keys](https://www.opendota.com/api-keys)
   I recommend getting an OpenDota API Key as otherwise collection of match data will take a long long time. Cost ~$1/10000 matches
4. Enter the API Key in data_collector/opendota_client.py
   ```python
   API_KEY="API_KEY_HERE"
   ```
5. Get a Free Gemini API Key from [https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)
   Gemini API is free to use for low-impact calls. Since the project makes 1 call everytime you run it shouldn't be an issue.
6. Enter the API Key in llm_explainer/explainer.py
   ```python
   API_KEY="API_KEY_HERE"
   ```

## Usage

### Collecting Data

After entering your OpenDota API Key, edit collector.py for how many hundreds of matches you want to collect.

```python
asyncio.run(collect_and_store(HUNDREDS_OF_MATCHES))
```

Then you can run using the following.

```sh
python -m data_collector.collector
```

### Training the Model

After collecting data, run the train_model script to train the model.

```sh
python -m ml_recommender.train_model
```

After the first run of this script, the dataset should be serialized into dataset.pkl so you can comment out these two lines.

```python
dataset = rec.prepare_dataset()
dataset.to_pickle("dataset.pkl")
```

In subsequent runs if you want to tune the parameters of the model training, edit the params dict in the train_model method.

```python
def train_model(dataset):
```

### Recommending Items (No LLM Explanation)

Run recommender.py for a raw list of top 10 items by score.

```sh
python -m ml_recommender.recommender
```

### Recommending Items With Explanation

Run the explainer script.

```sh
python -m llm_explainer.explainer
```

## Contact

Ryan Kim - ryankim2327@gmail.com
Project Link: [https://github.com/bosssburger/Dota-2-Item_Recommender](https://github.com/bosssburger/Dota-2-Item_Recommender)
