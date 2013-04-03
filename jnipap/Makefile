DEP = -classpath lib/ws-commons-util-1.0.2.jar:lib/xmlrpc-common-3.1.3.jar:lib/xmlrpc-client-3.1.3.jar
JFLAGS = -g -source 1.4 -Xlint $(DEP)
JC = javac
JAR = jar
JARFILE = jnipap.jar
JARFLAGS = cf $(JARFILE)

default: classes

classes:
	$(JC) $(JFLAGS) jnipap/*.java

jar: classes
	$(JAR) $(JARFLAGS) jnipap/*.class

clean:
	$(RM) jnipap/*.class $(JARFILE)
