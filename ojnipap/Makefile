DEP = -classpath .:../jnipap/jnipap.jar:./lib/ojdbc5.jar
JFLAGS = -g -Xlint $(DEP)
JC = javac
JAR = jar
JARFILE = ojnipap.jar
JARFLAGS = cf $(JARFILE)

default: classes

jnipap:
	cd ../jnipap && make jar

classes: jnipap
	$(JC) $(JFLAGS) -source 1.4 ojnipap/*.java

jar: classes
	$(JAR) $(JARFLAGS) ojnipap/*.class

clean:
	$(RM) *.class ojnipap/*.class $(JARFILE)
