## Qengine - The Basics

This details the basic structure of how a Qengine question is written.

#### Qengine Blocks
Qengine runs **blocks** that call a service to assemble something for you. Blocks look like this:
```
{%service:namespace:conditional
# block code goes here
%}
```
* **service**
	- The block type to run
* **namespace**
	- If your block generates any variables, they will be available in other blocks using this namespace. i.e. `namespace.variable`
* **conditional**
	- This is optional. you can set your block to run only if the conditional variable is set to 1. If not set, the block will always run.

#### Qengine Steps
Qengine runs every block within a step and then sends content to a quiz front-end.  Steps are separated like this:
```
@@@@conditional
```
* **conditional**
    - This is optional. If set, the following step will only run if the conditional variable exists (its value does not matter). If the variable does not exist, the previous step will be rerun.
    - **!!!** *important →* Quiz front-ends will often submit a student's question input, without any button variables, if the student clicks to a different question in the quiz. This allows you the option to process the question input or ignore it. If you want to require a button click for submission, make sure to use a conditional!

#### Qengine Variables
Variables are some content that can be respresented in plain text.

You can genereate variables with blocks and use them in other blocks by wrapping them with `@@`. i.e. `@@myBlockNameSpace.myVariable@@`

**!!!** *important →* `qengine` is a reserved namespace. It is used to store variables provided by Qengine or the quiz front-end. The only guaranteed variable is `randomseed`, which is a random number assigned to each student's quiz attempt. This allows you to generate randomized versions of questions for each student.

#### Qengine Resources
A resource is anything that cannot be represented with plain text, like an image, audio, or video.

If your code generates a resource, like an image, that resource must be given a variable name that starts with an underscore. i.e. `_myimage`

You can then use a Qengine shortcode to insert that resource into a question (read the [shortcodes.md](shortcodes.md) file on how to do that)

#### A Very Simple Example
```
{%qhtml:mySimpleExample
<p>Enter the number 10</p>
~~~question.answer:NUMBER:Enter your answer here~~~
~~~question.submit:SUBMIT:Submit Answer~~~
%}

@@@@question.submit

{%python2:myGradingBlock
grade = (@@question.answer@@ == 10) * 1
%}

{%qans:myGrade
@@myGradingBlock.grade@@
%}

{%qhtml:myResponse
<p>Your answer has been submitted.</p>
%}
```

1. The **qhtml** block is used to create the html form that is the question.

2. That is every block in step 1, so the form is sent to the student.

3. Let's say the student enters an answer and clicks the submit button.

4. Since the student clicked the submit button `student.submit` will exist, thus, the `@@@@student.submit` conditional is met and the next step is run.

5. The **python2** block is run, which runs python 2.7 code. This code checks if the student's answer is equal to ten. The variable `grade` becomes 1, if true and 0, if false.

6. The **qans** block returns a grade between 0 & 1 to the quiz front-end. In this case, the `myGradingBlock.grade` variable from the python2 block is used for the grade.

7. Finally, a **qhtml** block returns some text to the quiz front-end.
