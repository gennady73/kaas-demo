FROM registry.redhat.io/amq-streams/kafka-42-rhel9@sha256:ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d
USER 0
COPY sink /opt/r2-sink
COPY sink-guard.sh /opt/r2-sink/sink-guard.sh
RUN chmod 0555 /opt/r2-sink/sink-guard.sh && chmod -R a+rX /opt/r2-sink && mkdir -p /var/lib/r2 && chgrp 0 /var/lib/r2 && chmod g+rwx /var/lib/r2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/r2-sink python3 -c "import ssl, sqlite3, server, store, verify_export; print('R2_SINK_MODULE_IMPORT_OK')"
ENV HOME=/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 1001:0
WORKDIR /tmp
ENTRYPOINT ["/opt/r2-sink/sink-guard.sh"]
CMD []
