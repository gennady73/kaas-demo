FROM registry.redhat.io/amq-streams/kafka-42-rhel9@sha256:ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d
USER 0
COPY k6 /usr/local/bin/k6
COPY r2 /r2
COPY client-guard.sh /opt/r2/client-guard.sh
RUN chmod 0555 /usr/local/bin/k6 /opt/r2/client-guard.sh && chmod -R a+rX /r2 && command -v timeout && printf '%s  %s\n' '7405cc006c1d05d2748aee1955bfd3db6e3edf4e6f723dd997e060bd22c6525b' /usr/local/bin/k6 | sha256sum -c -
ENV HOME=/tmp K6_NO_USAGE_REPORT=true
RUN /usr/local/bin/k6 inspect /r2/inspect.js
USER 1001:0
WORKDIR /tmp
ENTRYPOINT ["/opt/r2/client-guard.sh"]
CMD []
