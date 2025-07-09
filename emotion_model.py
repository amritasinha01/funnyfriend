import joblib

def load_emotion_model(path='emotion_model.pkl'):
    return joblib.load(path)
