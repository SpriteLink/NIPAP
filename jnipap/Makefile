DEP = -classpath .:./jnipap.jar:lib/ws-commons-util-1.0.2.jar:lib/xmlrpc-common-3.1.3.jar:lib/xmlrpc-client-3.1.3.jar:/usr/share/java/junit4.jar
JFLAGS = -g -Xlint $(DEP)
JC = javac
JAR = jar
JARFILE = jnipap.jar
JARFLAGS = cf $(JARFILE)

default: classes

classes:
	$(JC) $(JFLAGS) -source 1.4 jnipap/*.java

jar: classes
	$(JAR) $(JARFLAGS) jnipap/*.class

test: classes
	$(JC) $(JFLAGS) JnipapTester.java
	#junit JnipapTester
	java $(DEP) org.junit.runner.JUnitCore JnipapTester

clean:
	$(RM) *.class jnipap/*.class $(JARFILE)
