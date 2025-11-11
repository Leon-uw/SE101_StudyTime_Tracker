import pytest
import logging
from src import connect2DB
from unittest.mock import patch

class Test_connection:
    #success
    def test_connection_success(self):
        logging.info("Testing successful connection")
        connection, curs = connect2DB.connection()
        assert connection is not None, "Should successfully return connection"
        assert curs is not None, "Should have a cursor ready"
        curs.close()
        connection.close()
    #success w/cursor
    def test_connection_creating_cursor(self):
        logging.info("Testing successful cursor creation")
        connection, curs = connect2DB.connection()
        assert curs is not None, "should have a cursor ready to go"
        assert hasattr(curs, 'execute'), "Should successfully return a cursor"
        #assert curs is not None, "Should have a cursor ready"
        curs.close()
        connection.close()
    #testing successful closure
    def test_connection_close(self):
        logging.info("Testing if connection closes")
        connection, curs = connect2DB.connection()
        assert connection.is_connected(), "Should have the connection up now"
        curs.close()
        connection.close()
        assert not connection.is_connected(), "Should successfully close connection"
    #testing failure handling
    @patch('src.connect2DB.mysql.connector.connect')
    def test_connection_failure(self, mock_connect):
        logging.info("Testing connection issues")
        mock_connect.side_effect = Exception("Connection failed!")

        with pytest.raises(Exception):
            connect2DB.connection()

