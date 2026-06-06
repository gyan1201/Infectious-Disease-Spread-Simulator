java -Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory \
  -Dlog.rootDirectory=logs \
  -Dfile.prefix=atl-basic \
  -Dsimulation.test=bias \
  -jar ../target/vanilla-0.1-jar-with-dependencies.jar \
  -configuration atl.5k.properties \
  -decision.bank llm.atl.csv \
  -bias.config bias.llm.properties \
  -bias.single.config bias.single.properties \
  -until 25920
