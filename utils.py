from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from collections import Counter
from wordcloud import STOPWORDS
custom_stopwords = STOPWORDS.union({'word1', 'word2'})

def flatten_one_level(d, sep='_'):
    """
    Flattens a dictionary by one level, combining nested keys with a separator.
    
    Args:
        d (dict): The dictionary to flatten
        sep (str): The separator to use between keys (default: '_')
        
    Returns:
        dict: A flattened dictionary with combined keys
    """
    flattened = {}
    for key, value in d.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                new_key = f"{key}{sep}{sub_key}"
                flattened[new_key] = sub_value
        else:
            flattened[key] = value
    return flattened



def create_wordcloud(text, title="Word Cloud", max_words=100, width=800, height=400, 
                    background_color='white', colormap='viridis', stopwords={}):
    """
    Create a word cloud from text.
    
    Args:
        text (str): The text to create word cloud from
        title (str): Title for the plot
        max_words (int): Maximum number of words to display
        width (int): Width of the word cloud image
        height (int): Height of the word cloud image
        background_color (str): Background color of the word cloud
        colormap (str): Matplotlib colormap for the words
        stopwords (set): Set of words to exclude from the word cloud
    """
    stopwords = stopwords.union(custom_stopwords)
    # Basic text cleaning
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    
    # Create word cloud
    wordcloud = WordCloud(
        width=width,
        height=height,
        max_words=max_words,
        background_color=background_color,
        colormap=colormap,
        stopwords=stopwords
    ).generate(text)
    
    # Display the word cloud
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title)
    plt.tight_layout()
    plt.show()
    
    # Return the word frequencies
    word_freq = Counter(text.split())
    return word_freq