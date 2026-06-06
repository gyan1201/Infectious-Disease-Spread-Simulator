java -Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory \
  -Dlog.rootDirectory=logs \
  -Dfile.prefix=atl-key-event \
  -Dsimulation.test=bias \
  -jar ../target/vanilla-0.1-jar-with-dependencies.jar \
  -configuration atl.5k.properties \
  -decision.bank llm.atl.S.key-event.csv \
  -bias.config bias.llm.S3.properties \
  -bias.single.config bias.single.properties \
  -until 25920
