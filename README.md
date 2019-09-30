# Robust Journey Planning

Lab in Data Science (EE-490) final assignment.   
  
Group: **DataBrewers**  
  
Team members:
- [Mathias Gonçalves](https://github.com/magoncal)
- [Julien Heitmann](https://github.com/jheitmann)
- [Louis Landelle](https://github.com/louislandelle)

You will find the final report in `journey-planning.ipynb` in the root folder.
You can see our presentation video in `DSLab Presentation Data-Brewers.mp4` in the root folder, as well as our slides.

## Core
Given a desired departure, or arrival time, our route planner will compute the fastest route between two stops within a provided uncertainty tolerance expressed as interquartiles - we have called this q-value. For instance, “what route from A to B is the fastest at least Q% of the time if I want to leave from A (resp. arrive at B) at instant T”. Note that uncertainty is a measure of a route not being feasible within the time computed by the algorithm. Our algorithm of choice is an adapted version (stochastic) of the Connection Scan Algorithm (https://arxiv.org/abs/1703.05997) which makes use of the historical SBB data to construct Cumulative Distribution Functions of delays.

## Web demo
Our web demo runs on a Flask web server from a jupyter notebook and you can access the demo from the browser.
If you run from the SSH, you need to visit the address IP where the notebook runs (usually 10.90.38.18) or locally, in localhost/127.0.0.1 with :2019 or the new port you have chosen if you modified the port in the notebook.

`Warning: you should use Flask 1.0.2 or 1.0.3 for this to work properly.`
