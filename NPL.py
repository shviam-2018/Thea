from sklearn.pipeline import Pipeline 
from sklearn.naive_bayes import MultinomialNB 
from sklearn.feature_extraction.text import CountVectorizer as cv 
from sklearn.feature_extraction.text import TfidfTransformer 

#building our NLP model using naive bayes as classifier 
pipeline = Pipeline([('bow', cv(analyzer=function_preprocess)), 
					('tfidf', TfidfTransformer()), 
					('classifier', MultinomialNB()), 
					]) 
pipeline.fit(data, emotional_class) 