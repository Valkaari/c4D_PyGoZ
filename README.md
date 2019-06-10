rewrite the GOZ for cinema4D R20 in python.


we catch the sys arguments to check if zbrush is launching cinema4D and calling the coffee script.



know issue :
after the first launch of cinema4D we can't catch sys.arg anymore so users must activate the plugin to update/reload the mesh.


on OSX sys.argv is empty so the script is not launched not even a sigle time


Scale Master Branch

When you are using Scale Master things are a bit different.
Scale number have been change to it's better now.
But if you are not using Scale Master this will create tiny mesh inside cinema4D. That's why i have separate branche
thanks https://github.com/edenexposito for the fix
