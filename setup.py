from setuptools import setup, find_packages

setup(
    name="dota_item_recommender",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "recommend=ml_recommender.recommender:main"
        ]
    }
)

