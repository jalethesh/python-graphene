
FROM ubuntu:latest
RUN apt-get -y update --fix-missing
# RUN apt-get -y install git
RUN apt-get -y install make


COPY . /app

EXPOSE 5000
RUN echo "#!/bin/bash\n" > /startscript.sh
RUN echo "cd /app\n" >> /startscript.sh
# RUN echo "ls\n" >> /startscript.sh
# RUN echo "printenv\n" >> /startscript.sh
# RUN echo "mkdir github\n" >> /startscript.sh
# RUN echo "cd github\n" >> /startscript.sh
# RUN echo "git clone \$github\n" >> /startscript.sh
# RUN echo "cd *\n" >> /startscript.sh
RUN echo "make dockertest\n" >> /startscript.sh
RUN chmod +x /startscript.sh
CMD /startscript.sh
