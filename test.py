from fabric_forked import Connection

with Connection('10.42.0.1', user='romanin', port=22, connect_kwargs={'password': '0000'}) as connection:
    result = connection.run('neofetch')