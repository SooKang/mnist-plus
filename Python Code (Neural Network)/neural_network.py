#!/usr/bin/env python

from __future__ import division
import math
import numpy as np
import random
import sys
from nolearn.dbn import DBN
from sklearn.cross_validation import cross_val_score, train_test_split
from sklearn.datasets import load_iris
from sklearn.decomposition import RandomizedPCA
from sklearn.preprocessing import scale
from sklearn import metrics

np.random.seed(2)
TEST_IRIS = False
ENABLE_DEBUG = True

def g(x):
  return 1 / (1 + math.exp(-x))

def g1(x):
  return (1 - g(x))*g(x)

class NeuralNetwork:
  def __init__(self, layer_sizes=None, epochs=10, alpha=0.1):
    self.layer_sizes = layer_sizes
    self.epochs = epochs
    self.alpha = alpha
    self.Nc = 0 # number of classes
    self.loss = 0

    self.W = [0] * (len(layer_sizes)-1) # weights
    self.A = [0] * len(layer_sizes) # activations
    for j in xrange(len(layer_sizes)):
      self.A[j] = np.zeros((layer_sizes[j], 1))
    for j in xrange(0, len(layer_sizes)-1):
      b = math.sqrt(6) / math.sqrt(layer_sizes[j] + layer_sizes[j+1])
      self.W[j] = np.random.uniform(-b, b, [layer_sizes[j+1], layer_sizes[j]+1])
    self.bias = [1] * len(layer_sizes)

  def forward_propagate(self, X):
    self.A[0] = X
    for j in xrange(1, len(self.layer_sizes)):
      A = self.W[j-1]
      B = np.append([self.bias[j-1]], self.A[j-1])
      B = B.reshape((B.shape[0], 1))
      Z = np.dot(A, B)
      for i, z in enumerate(Z):
        self.A[j][i] = g(z)

  def backward_propagate(self, X, Y):
    delta = [np.zeros((self.layer_sizes[l], 1)) for l in xrange(len(self.layer_sizes))]
    for l in xrange(len(self.layer_sizes)-1, 0, -1):
      if l == len(self.layer_sizes) - 1:
        delta[l] = self.A[l] - Y
        self.loss += np.linalg.norm(delta[l])
      else:
        D = np.append([self.bias[l-1]], self.A[l-1])
        D = D.reshape((D.shape[0], 1))
        Z = np.dot(self.W[l-1], D)
        if l+1 == len(self.layer_sizes) - 1:
          A = np.dot(self.W[l].T, delta[l+1])
        else:
          A = np.dot(self.W[l].T, delta[l+1][1:])
        B = np.append([self.bias[l]], np.array([g1(z) for z in Z])).reshape(A.shape)
        delta[l] = np.multiply(A, B)

    for l in xrange(len(self.layer_sizes)-2, 0, -1):
      if l+1 == len(self.layer_sizes) - 1:
        A = delta[l+1]
      else:
        A = delta[l+1][1:]
      B = np.append([self.bias[l]], self.A[l])
      B = B.reshape((B.shape[0], 1))
      self.W[l] -= self.alpha * np.dot(A, B.T)

  def fit(self, X, Y):
    self.Nc = np.unique(Y).shape[0]
    self.Nx = X.shape[0]
    indices = range(X.shape[0])
    for iter in xrange(self.epochs):
      self.loss = 0
      #random.shuffle(indices)
      for i, idx in enumerate(indices):
        if ENABLE_DEBUG and i > 0 and i % 1000 == 0:
          print i
        x = X[idx]
        y = np.zeros((self.Nc, 1))
        y[Y[idx]] = 1
        self.forward_propagate(x)
        self.backward_propagate(x, y)
      self.loss /= len(indices)
      #print "epoch: %d, loss: %f" % (iter, self.loss)

  def predict(self, X):
    pred = np.zeros((X.shape[0], 1))
    for i, x in enumerate(X):
      self.forward_propagate(x)

      # softmax
      zsum = np.sum([math.exp(z) for z in self.A[-1]])
      probs = [math.exp(z)/zsum for z in self.A[-1].T[0]]
      pred[i] = np.argmax(probs)
    return pred

def test_iris():
  iris = load_iris()

  X_train, X_test, Y_train, Y_test = train_test_split(scale(iris.data), iris.target, test_size=0.5, random_state=42)
  #clf = DBN( [4, 4, 3], learn_rates=1, epochs=1, momentum=0, learn_rate_decays=1, minibatch_size=X_train.shape[0])
  scores = []
  for epochs in xrange(100):
    print epochs
    clf = NeuralNetwork([4,4,3], alpha=0.1, epochs=epochs)
    clf.fit(X_train, Y_train)
    pred = clf.predict(X_test)
    score = metrics.f1_score(Y_test, pred)
    scores.append(score)

  import matplotlib.pyplot as plt
  plt.plot(scores)
  plt.xlabel('epochs')
  plt.ylabel('f1 score')
  plt.savefig('graph.png')

  """
  print("f1-score:   %0.3f" % score)

  print("classification report:")
  print(metrics.classification_report(Y_test, pred))

  print("confusion matrix:")
  print(metrics.confusion_matrix(Y_test, pred))
  """

if TEST_IRIS:
  ENABLE_DEBUG = False
  test_iris()
  sys.exit(0)

X = np.load('../blobs/X_train.npy')
Y = np.load('../blobs/Y_train.npy')
select = RandomizedPCA(n_components=100, whiten=True)
X = select.fit_transform(X)
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
clf = NeuralNetwork([X.shape[1],2*X.shape[1],X.shape[1],X.shape[1]//2,10], alpha=0.1, epochs=1)
clf.fit(X_train, Y_train)
pred = clf.predict(X_test)

score = metrics.f1_score(Y_test, pred)
print("f1-score:   %0.3f" % score)

print("classification report:")
print(metrics.classification_report(Y_test, pred))

print("confusion matrix:")
print(metrics.confusion_matrix(Y_test, pred))
