rewrite the GOZ for cinema4D R20 in python.


we catch the sys arguments to check if zbrush is launching cinema4D and calling the coffee script.



know issue :
after the first launch of cinema4D we can't catch sys.arg anymore so users must activate the plugin to update/reload the mesh.


on OSX sys.argv is empty so the script is not launched not even a sigle time



If you are using Scale Master, please use the Scale Master Banch
