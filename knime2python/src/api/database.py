import mysql.connector
import logging
import time
from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR


class Database():
    def __init__(self, host, port, user, password, schema, output_table, baseyear):
        self.logger = logging.getLogger(__name__)
        self.schema = schema
        self.output_table = output_table
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.baseyear = baseyear

        tries = 15
        wait = 5
        for r in range(tries):
            try:
                self.logger.info('Connecting to DB, attempt {}/{}'.format(r+1, tries))
                self.conn = mysql.connector.connect(host=host, port=port, user=user, password=password)
                break
            except:
                self.logger.error('Error connecting to the database.')
                self.logger.info('Waiting for {} seconds'.format(wait))
                time.sleep(wait)
                if r == tries:
                    raise

        uri = 'mysql://{}:{}@{}:{}/{}'.format(user, password, host, port, schema)  # Changed by tobi
        self.engine = create_engine(uri)  # Changed by tobi

    def _query(self, query):
        """Generic function to issue a query to the database.

        :param config: database configuration dictionary
        :param query: query to run
        :return: dict with columns and data as list of tuples
        """

        # Recreating the connection is an overkill, but seems to overcome
        # connection problems with long Knime running times.
        try:
            self.conn = mysql.connector.connect(host=self.host, port=self.port, user=self.user, password=self.password)
        except:
            self.logger.error('Error connecting to the database.')
            raise

        cursor = self.conn.cursor()

        try:
            cursor.execute("USE {database};".format(database=self.schema))
            cursor.execute(query)
        except:
            self.logger.error('Error running query: {}'.format(query))
            raise

        if cursor.description:
            # Column names
            fields = [i[0] for i in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            return {'columns': fields,
                    'data': data
                    }
        else:
            return None

    def recreate_db(self):
        """Removes and recreate the database.

        :param config: database configuration dictionary.
        :return: bool indicating success or failure.
        """

        cursor = self.conn.cursor()

        query = "DROP SCHEMA {schema}".format(schema=self.schema)
        try:
            self.logger.debug('Running query: {}'.format(query))
            cursor.execute(query)
        except:
            self.logger.error('Error while running query: {}'.format(query))

        query = "CREATE SCHEMA {schema}".format(schema=self.schema)
        try:
            self.logger.debug('Running query: {}'.format(query))
            cursor.execute(query)

            # Create a levers_position_list to keep track of the run scenarios
            dict = {"id": "init"}
            df_id = pd.DataFrame(dict, index=["init"])
            df_id.to_sql(name="levers_position_list", con=self.engine, if_exists="append", index=False, dtype={'id': MEDIUMTEXT})

            return True
        except mysql.connector.errors.DatabaseError as e:
            self.logger.warning('Database {schema} already exists. It is usually caused by a another thread running in parralel'.format(schema=self.schema))
            return True
        except:
            raise
            return False

    def save_cache_db(self, levers_position, output_table, first_run):
        """Save a table to a DB using the lever position as name

        :param config: database connection dictionary
        :param levers_position: string of lever_position
        :param table_output: table to be saved as output
        :return: bool indicating success or failure.
        """

        "ALTER TABLE `levers`.`node_1206_out_1` "
        "CHANGE COLUMN `idx` `idx` VARCHAR(255) NULL DEFAULT NULL ,"
        "ADD INDEX `index_table` (`idx` ASC);"
        ";"

        try:
            if self.scenario_in_db(levers_position):
                self.logger.info("The scenario {scenario} was pushed to the database by another thread.".format(scenario=levers_position))
            else:
                # FIXME: lever position table not needed anymore

                dict = {"id":levers_position}
                df_id = pd.DataFrame(dict, index=[levers_position])
                df_id.to_sql(name="levers_position_list", con=self.engine, if_exists="append", index=False)

                # FIXME
                # Potential improvements:
                # - Separate historical from future data and save only future (decrease first the size of the model in the memory)
                # - Test if compression changes overall roundtrip time

                df_results=pd.DataFrame([[levers_position, output_table]], columns=['idx', 'data'], index=[levers_position])
                df_results.to_sql(name=self.output_table, con=self.engine,
                                  if_exists='append', index=False, chunksize=28,
                                  dtype={'idx': MEDIUMTEXT, 'data':LONGBLOB}
                                  )

                # for key, df in output_table.items():
                #     table = df.copy()
                #     table['idx'] = levers_position
                #     if 'Years' in table.columns:
                #         table.loc[:, 'Years'] = table['Years'].astype('int')
                #         mask = (table['Years']>self.baseyear)
                #         table.loc[mask,:].to_sql(name=key, con=self.engine, if_exists='append', index=False, chunksize=28)
                #         if first_run:
                #             table['idx'] = "historical"
                #             mask = (table['Years']<=self.baseyear)
                #             table.loc[mask,:].to_sql(name=key, con=self.engine, if_exists='append', index=False, chunksize=28)
                #     else:
                #         self.logger.info("Column Years not present in table "+key+". Saving the whole table to the db.")
                #         table.to_sql(name=key, con=self.engine, if_exists='append', index=False, chunksize=28)
            return True
        except:
            raise
            return False

        #check if table exist in database

        # #create table
        # query = ("CREATE TABLE {name}({data})").format(name=levers_position, data=output_table)
        #
        # try:
        #     self.logger.debug('Running query: {}'.format(query))
        #     self._query(query)
        #     return True
        # except:
        #     raise
        #     return False

    def query_cache_db(self, levers_position):
        """Query a DB table using a set of filters on levers and column (metric)

        :param levers_position: string of lever_position
        :param output_nodes: dictionary of tables asked to the db
        :return: dict of dataframes base on output_nodes dictionary
        """
        results = {}

        try:

            query = ("SELECT * FROM {table} WHERE idx = \'{levers_position}\'").format(table=self.output_table, levers_position=levers_position)
            results = pd.read_sql_query(query, con=self.engine).loc[0,'data']

            # for table_name in output_nodes:
            #     query = ("SELECT * FROM {table} WHERE idx = {levers_position} or idx = 'historical'").format(table=table_name, levers_position = levers_position)
            #     result = pd.read_sql_query(query, con=self.engine)
            #     if 'Years' in result.columns:
            #         result = result.sort_values(by=['Years'])
            #         result["Years"] = result["Years"].astype(str)
            #     results[table_name] = result.drop('idx', axis=1)
        except:
            raise
            return []

        return results

    def scenario_in_db(self, levers_position):
        """Query the scenario index and check if the scenario already exist

        :param levers_position: string of lever_position
        :return: True if scenario in db, False if not
        """

        try:

            query = ("SELECT * FROM levers_position_list WHERE id = \'{levers_position}\'").format(levers_position = levers_position)
            result = pd.read_sql_query(query, con=self.engine)
        except:
            raise
            return False

        # if the result dataframe is empty, it means that the table does not contain the scenario
        return not result.empty


    def test_cache_db(self, levers_position, output_table):
        """test if a specific levers_position is stored in the db

        :param config: database connection dictionary
        :param levers_position: string of lever_position
        :return: bool indicating success or failure.
        """

        # ON PROGRESS - NOT FUNCTIONAL
        try:
            output_table.to_sql(name="levers_position_list", con=self.engine, if_exists="append", index=False)
            return True
        except:
            raise
            return False

    def query_output_db(self, filters, columns):
        """Query a DB table using a set of filters on levers and column (metric)

        :param config: database connection dictionary
        :param filters: dict of levers positions
        :param columns: list of columns
        :return: dict with columns and data as list of tuples
        """

        column_list = ','.join(['`' + c + '`' for c in columns])

        query = ("SELECT {columns}, Years, Country FROM {table} WHERE ").format(columns=column_list, table=self.output_table)

        for lever, value in filters.items():
            if value:
                query += "`" + str(lever) + "`=" + str(value) + " AND "
        query += "1=1"

        # This section required to get the history (lever values = 0)
        query += (" UNION SELECT {columns}, Years, Country FROM {table} WHERE ").format(columns=column_list, table=self.output_table)
        for lever, value in filters.items():
            if value:
                query += "`" + str(lever) + "`=0 AND "
        query += "1=1"
        query += " ORDER BY Years ASC"

        try:
            self.logger.debug('Running query: {}'.format(query))
            result = self._query(query)
        except:
            raise
            return []

        return self._query(query)


    def output_db_lever_test(self, filters):
        """Test if a set of lever positions exists in the database.

        :param config: database configuration dictionary
        :param filters: lever positions
        :return: bool: True if results exist, False otherwise
        """

        #query = ("USE {database}; SELECT count(*) FROM {table} WHERE ").format(database=self.schema, table=self.output_table)
        query = ("SELECT count(*) FROM {table} WHERE ").format(database=self.schema,
                                                                               table=self.output_table)
        for lever, value in filters.items():
            if value:
                query += "`" + str(lever) + "`=" + str(value) + " AND "
        query += "1=1"

        query += " GROUP BY "
        for lever, value in filters.items():
            if value:
                query += "`" + str(lever) + "`,"
        query = query[:-1]

        try:
            self.logger.debug('Running query: {}'.format(query))
            result = self._query(query)
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_NO_SUCH_TABLE:
                self.logger.warning("Table {} doesn't exist".format(self.output_table))
                return []
            else:
                raise

        if result:
            return len(result.get('data')) > 0
        else:
            return 0


#db = Database('127.0.0.1', 3306, 'root', '7VupwgCxBQVZ', 'eucalc', 'output', 2015)
#engine = db.engine
#conn = engine.connect()
#conn.execute('CREATE TABLE test(name TEXT)')

