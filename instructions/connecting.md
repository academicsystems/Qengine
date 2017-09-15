## Qengine - Directory Structure & Connections

This details how and where question files should be placed along with how to connect a quiz front-end to Qengine.

#### Directory Structure
Qengine questions are placed in a directory called `questions` in the root directory of the Qengine repo (in other words, the same directory that contains `qengine.py`).

For example: `./questions/linear_algrebra/lu_factorization/1.1/question`

Questions are separated into `question_bank`, `question_base`, `question_id`, and the `question` file itself.
* **question_bank**
    - Question banks hold groups of questions that all use the same engine
    - They must be named with only letters and underscores
* **question_base**
    - Question bases are essentially equivalent to classes
    - They must be named with only letters and underscores
* **question_id**
    - Question IDs are versions of questions. Because a question might change while a student is still taking a quiz that uses it, or because a quiz might want to continue using a previous version, updates to a quiz should use a new question ID.
    - They must in the major.minor format, like: 1.0
* **question**
    - The question must be in a file named **question**. The extension does not matter and is ignored, although the question should be in plain text.

The final directory structure should like:
```
./
|---questions/
    |---question_bank/
        |---question_base/
            metadata
            |---question_id/
                question
```

**!!!** *important →* You must add the `metadata` file to successfully connect to a question. The file should be YAML and can contain any general information about the question.

#### Connecting A Front-End

Qengine currently follows only the Opaque REST protocol. You should use an Opaque REST protocol enabled plugin or front-end. Connecting to Qengine should be a 2 step process:

* Add a connection to Qengine. This will involve adding the following:
    * url to the engine
    * the question bank to use
    * (optional) a passkey

To test the connection, the plugin will request `/getEngineInfo`. That should return a properly formatted response if successful. There might not be any data to display, but if there is, it's usually some general information about the engine itself. 

* Add the question to a quiz. This will involve adding the following:
    * the question version to use
    * the question id to use


To test the question, the plugin will request `/getQuestionMetadata`. That should return a properly formatted response if successful. Again, there might not be any data to display, but if there is, it's usually some general information about the question itself. (the data returned is from the question's `metadata` file)




