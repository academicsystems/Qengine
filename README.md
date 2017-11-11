[![Build Status](https://travis-ci.org/academicsystems/Qengine.svg?branch=master)](https://travis-ci.org/academicsystems/Qengine)

# Qengine
A powerful quiz engine for learning management systems

## How It Works

Qengine is a back-end that assembles resources into a quiz. There are two important attributes that make Qengine powerful:

1. Each student is assigned a random number identifier ("random seed")

That means you can use the random number to generate a different question version for each student.

2. Qengine can get resources from microservices.

That means you can generate resources using code like SageMath, Python, Javascript, etc. That also means you can use code to autograde students' answers.

## How To Write Questions

You can learn how by reading the files in the `instructions` folder.

## Running Qengine

Edit `default-configuration.yaml` and rename to `configuration.yaml`

Then run: `python -m qengine`

## Running Single Test

`python -m tests.[testname]`

## Running All Tests

`python -m unittest discover tests`

## Support

Qengine is actively developed at the University of Colorado Boulder and maintained by [Academic Systems](https://academic.systems)
