## Qengine - Shortcodes

The following is a list of shortcodes that can be used in the **qhtml** block to insert HTML form inputs or resources like images.

#### Question HTML Input Shortcodes
HTML form inputs require special attributes to work with quiz front-ends. Because of this, convenient shortcodes have been created to generate the HTML inputs for you. They are listed below:

```
~~~namespace.variable:TEXT:placeholder text~~~
~~~namespace.variable:NUMBER:placeholder text~~~
~~~namespace.variable:TEXTAREA-20:placeholder text~~~
~~~namespace.variable:SUBMIT:button text~~~
~~~namespace.variable:RESET:button text~~~
```

* TEXT
    - html input, type="text" > a single line text box
* NUMBER
    - html input, type="number" > a single line number box
* TEXTAREA-#
    - html textarea, rows="#" > a multiple line text box
* SUBMIT
    - html input, type="submit" > a submit button
* RESET
    - html input, type="text" > a button that resets all inputs

The student's input will be available in the question's next step with `namespace.variable`

#### Question Resource Shortcodes
Resources require special URLs for src attributes. Because of this, convenient shortcodes have been created to generate elements that use the src attribute. They are listed below:

```
~~~namespace.resource:AUDIO~~~
~~~namespace.resource:EMBED~~~
~~~namespace.resource:IMAGE~~~
~~~namespace.resource:SCRIPT~~~
~~~namespace.resource:VIDEO~~~
```

* AUDIO
    - html audio > plays an audio file
* EMBED
    - html embed > embeds an external application
* IMAGE
    - html image > displays an image
* SCRIPT
    - html script > loads client-side javascript
* VIDEO
    - html video > plays a video file


