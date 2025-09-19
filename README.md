# Trustedcloud-smart-agent

**to build the image**
```bash=
docker build -t trusted-cloud-agent:dev .
```

**to run the container**
```bash=
# for self-build
docker run -p 8080:8080 -d trusted-cloud-agent:dev agent_main:app --host
# or using image from docker hub
docker run -p 8080:8080 -d kanic1111/trusted-cloud-agent:dev   agent_main:app --host
```

**you can test the server if you enter**

**http://[your ip address]:8080/**

**API document in**

**http://[your ip address]:8080/docs**
