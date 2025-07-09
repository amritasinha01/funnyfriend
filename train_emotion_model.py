import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# Training data: emotions and sample texts
data = {
    'text': [
        # Happy
        "I am so happy today!", "I feel excited", "What a beautiful day", "I'm feeling great", "happy",

        # Sad
        "I am really sad", "This is depressing", "I feel terrible", "sad",

        # Angry
        "I'm very angry", "This makes me furious", "I hate this", "angry",

        # Funny
        "I'm on a seafood diet. I see food, I eat it.",
        "My dog thinks I'm hilarious. That’s enough.",
        "If I had a dollar for every smart thing I say, I'd be broke.",
        "Life’s too short to be serious all the time — so if you can't laugh, call me.",
        "My mirror and I had a staring contest. I lost.",
        "Why be moody when you can shake your booty?",
        "Sometimes I talk to myself. We both laugh.",
        "I'm not lazy, I'm just on power-saving mode.",
        "My humor is 80% sarcasm, 20% bad timing.",
        "I laugh at my own jokes so you don't have to. is not it funny.",

        # Bold
        "I know my worth, I don’t need validation.",
        "I’m not afraid to stand out.",
        "I speak my mind, always.",
        "I don't follow the crowd, I lead it.",
        "Confidence is my middle name.",
        "I don't back down from challenges.",
        "I stand tall, even when I stand alone.",
        "I'm unapologetically me.",
        "Being bold isn't a choice, it's who I am.",
        "I'm fearless when it matters.",

        # Neutral
        "I don't know what to feel", "Meh", "Okay, I guess", "Neutral",

        # Dumb
        "totally dumb",
        "That was so dumb I forgot how to breathe",
        "Why did I even say that... dumb dumb dumb",
        "My brain just stopped working 💀",
        "This is peak stupidity 😂",
        "That joke broke my last brain cell",
        "I lost 10 IQ points reading this",
        "Certified dumb moment",
        "This is the dumbest thing I've ever seen",
        "Dumber than a brick wearing sunglasses",
        "No thoughts, just dumb",

        # New Emotions:
        "I'm feeling anxious and uneasy.",  # Anxiety
        "My worries just won’t stop circling in my mind.",  # Anxiety
        "I feel trapped in my own anxious thoughts.",  # Anxiety
        "anxiety", # Anxiety

        "I feel hopeless and empty.",  # Depression
        "It’s hard to even get out of bed today.",  # Depression
        "Everything feels dull and meaningless.",  # Depression
        "Depression", #Depression
        "Depressed", #Depression
        "I am feeling Depressed", #Depression

        "I’m feeling overwhelmed by everything.",  # Stress
        "My head feels like it's about to explode.",  # Stress
        "There’s just too much on my plate right now.",  # Stress
        "Stress",  # Stress
        "I feel stressed",  # Stress
        "I can't handle this pressure anymore.",  # Stress
        "I'm so stressed out, I can't even think straight.",  # Stress
        "My stress levels are through the roof.",  # Stress
        "Everything feels like it's crashing down on me.",  # Stress
        "I feel like I'm drowning in stress.",  # Stress


        "I feel deeply thankful for all the support.",  # Gratitude
        "Grateful for the little things today.",  # Gratitude
        "I’m truly blessed to have such good friends.",  # Gratitude
        "Gratitude",  # Gratitude

        "I feel relieved after finishing my work.",  # Relief
        "That weight is finally off my shoulders.",  # Relief
        "Everything is calm now, finally.",  # Relief
        "Relief",  # Relief

        "I still believe better days are coming.",  # Hope
        "Holding on to hope even in tough times.",  # Hope
        "Hope is keeping me going.",  # Hope
        "Hope",  # Hope


        "I feel lonely even in a crowd.",  # Loneliness
        "Sometimes, I just wish someone understood me.",  # Loneliness
        "Silence feels louder when you’re alone.",  # Loneliness
        "Loneliness", # Loneliness
        "lonely", # Loneliness

        "I can’t stop feeling guilty about my mistake.",  # Guilt
        "I regret what I’ve done.",  # Guilt
        "The guilt is eating me up inside.",  # Guilt
        "Guilt",  # Guilt

        "I feel ashamed of myself.",  # Shame
        "Shame is such a heavy feeling to carry.",  # Shame
        "I wish I could hide from my past mistakes.",  # Shame
        "Shame", # Shame

        "Curiosity is making me question everything.",  # Curiosity
        "I want to learn more about this topic.",  # Curiosity
        "Why does everything work this way?",  # Curiosity
        "Curiosity", # Curiosity

        "I feel motivated to improve myself today.",  # Motivation
        "Let’s go! I’m ready to tackle anything.",  # Motivation
        "Motivation is rushing through my veins.",  # Motivation
        "Motivation", # Motivation
        "Motivated", # Motivation

        "I feel exposed sharing my thoughts openly.",  # Vulnerability
        "Vulnerability makes me nervous but honest.",  # Vulnerability
        "Sharing my story makes me feel vulnerable.",  # Vulnerability
        "Vulnerable", # Vulnerability

        "I’m feeling bored right now.",  # Bored
        "bore", # Bored
        "bored", # Bored

        "I’m feeling so hungry right now.",  # Hungry
        "My stomach is growling. I need food!",  # Hungry
        "I could really use a snack or meal.",  # Hungry
        "I'm starving.",  # Hungry
        "I just want to eat something delicious.",  # Hungry
        "I feel super hungry.",  # Hungry
        "All I can think about is food.",  # Hungry
        "Hungry",  # Hungry
        "I need to eat.",  # Hungry
        "Where's the food? I'm hungry.",  # Hungry

        "Feeling romantic and dreamy.",  # Romantic
        "romantic", # Romantic
        "I feel romantic today.",
        "I'm in a romantic mood.",
        "Love is in the air tonight.",
        "I'm thinking about romance and love.",
        "I'm dreaming of a romantic getaway.",
        "Romantic vibes are everywhere.",
        "I just want to cuddle and watch a romantic movie.",
        "I'm feeling all romantic and cozy."



    ],
    'emotion': [
        # Happy
        "happy", "happy", "happy", "happy", "happy",

        # Sad
        "sad", "sad", "sad", "sad",

        # Angry
        "angry", "angry", "angry", "angry",

        # Funny
        "funny", "funny", "funny", "funny", "funny",
        "funny", "funny", "funny", "funny", "funny",

        # Bold
        "bold", "bold", "bold", "bold", "bold",
        "bold", "bold", "bold", "bold", "bold",

        # Neutral
        "neutral", "neutral", "neutral", "neutral",

        # Dumb
        "dumb", "dumb", "dumb", "dumb", "dumb",
        "dumb", "dumb", "dumb", "dumb", "dumb", "dumb",

        # New Emotions:
        "anxiety", "anxiety", "anxiety", "anxiety",
        "depression", "depression","depression" ,"depression","depression","depression",
        "stress", "stress", "stress", "stress", "stress", "stress", "stress", "stress", "stress", "stress",
        "gratitude", "gratitude", "gratitude", "gratitude",
        "relief", "relief", "relief", "relief",
        "hope", "hope", "hope", "hope",
        "loneliness", "loneliness", "loneliness", "loneliness", "loneliness",
        "guilt", "guilt", "guilt", "guilt",
        "shame", "shame", "shame", "shame",
        "curiosity", "curiosity", "curiosity", "curiosity",
        "motivation", "motivation", "motivation", "motivation", "motivation",
        "vulnerability", "vulnerability", "vulnerability", "vulnerability",
        "bored", "bored" , "bored" ,
        "hungry", "hungry", "hungry", "hungry", "hungry", "hungry", "hungry", "hungry", "hungry", "hungry",
        "romantic", "romantic" , "romantic", "romantic" , "romantic", "romantic" , "romantic", "romantic" , "romantic", "romantic" ,
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# TF-IDF Vectorizer instead of CountVectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['text'])

# Logistic Regression model instead of Naive Bayes
model = LogisticRegression(max_iter=1000)
model.fit(X, df['emotion'])

# Save the model and vectorizer together
joblib.dump((model, vectorizer), 'emotion_model.pkl')
