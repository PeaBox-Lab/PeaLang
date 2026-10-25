from pealang.cloud_connectors import sftp
with sftp("sftp.example.com",username="user",private_key="id_ed25519",known_hosts="known_hosts") as c:
    frame=c.read_csv_frame("/inbound/data.csv")

