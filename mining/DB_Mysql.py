import time
import gc
import hashlib
import lib.settings as settings
import lib.logger
log = lib.logger.get_logger('DB_Mysql')

import MySQLdb

class DB_Mysql():
	def __init__(self):
		# DB Connection Handle
		self.MYSQL_CONNECTION = None
		# Shared Cursor
		self.MYSQL_CURSOR = None
		# Connection in progress
		self.CONNECTING = False

		log.debug("MySQL Database Initialization")

		required_settings = ['PASSWORD_SALT', 'DB_MYSQL_HOST', 
							 'DB_MYSQL_USER', 'DB_MYSQL_PASS', 
							 'DB_MYSQL_DBNAME', 'ARCHIVE_DELAY',
							 'DB_MYSQL_PORT']

		for setting_name in required_settings:
			if not hasattr(settings, setting_name):
				raise ValueError("%s isn't set, please set in config.py" % setting_name)

		self.salt = getattr(settings, 'PASSWORD_SALT')
		self.database_extend = hasattr(settings, 'DATABASE_EXTEND') and getattr(settings, 'DATABASE_EXTEND') is True

		self.connect()

# -------------------------- BEGIN MySQL Operational Functions ---------------------------------------

	def connect(self):
		# Now make a new connection
		self.CONNECTING = True

		try:
			log.info("Attempting to connect MySQL database server...")
			self.MYSQL_CONNECTION = MySQLdb.connect(
				getattr(settings, 'DB_MYSQL_HOST'), 
				getattr(settings, 'DB_MYSQL_USER'),
				getattr(settings, 'DB_MYSQL_PASS'), 
				getattr(settings, 'DB_MYSQL_DBNAME'),
				getattr(settings, 'DB_MYSQL_PORT')
			)

			# Setup the connection options
			self.MYSQL_CONNECTION.autocommit(True)
			log.info("MySQL database server Connected!")
			self.MYSQL_CURSOR = self.MYSQL_CONNECTION.cursor()

		finally:
			# We are done
			self.CONNECTING = False

	def close(self):
		log.info("Disconnecting MySQL database server.")
		try:
			self.MYSQL_CURSOR.close()
			self.MYSQL_CONNECTION.close()
			self.MYSQL_CONNECTION = None
			self.MYSQL_CURSOR = None
			gc.collect()
		except:
			# It may fail
			log.debug("DB Connection Already Closed.")
			pass

	def check_connection(self):
		# Ensure required objects are not None
		if self.MYSQL_CONNECTION is None or self.MYSQL_CURSOR is None:
			raise MySQLdb.OperationalError

		# Now ping the connection
		self.MYSQL_CONNECTION.ping()

		# All is good
		return True

	def reconnect(self, retries = 0):
		# Lets check the connection since it's state may have changed before we got here
		try:
			self.check_connection()
			# If all is good, then our work is done here
			return
		except:
			# It's still no good, let's proceed with execution of this reconnect function
			log.warning("MySQL connection still down.")

		# Maximum # of attempts
		if retries > 500:
			raise Exception('Maximum retry attempts exhausted while reconnecting to MySQL')

		try:
			# If a connection is already in process, lets just wait by throwing an excepton
			if self.CONNECTING:
				raise Exception("Database connection aready in process.")

			log.debug("Attempting Reconnect to MySQL database server.")
			# Close any existing connection and clean up remaining garbage
			self.close()

			# Atttmpt connection
			self.connect()
		except Exception as e:
			# Connection failed
			# Wait 5 seconds minium, 60 seconds maximum before retry
			retries = retries + 1
			waitime = (5 * retries) % 60
			log.error("MySQL database server reconnect attempt #%i failed: %s.  Waiting %i seconds" % (retries, e.args[0], waitime))
			time.sleep(waitime)
			self.reconnect(retries)

	def execute(self, query, args = None):
		log.debug("Executing Basic Query")
		log.debug("DB Query: %s" % query)
		log.debug("DB Values: %s" % args)

		try:
			# Ensure all is good
			self.check_connection()
			# Run the SQL
			self.MYSQL_CURSOR.execute(query, args)
		except MySQLdb.OperationalError:
			log.warning("MySQL connection lost during execute.")
			self.reconnect()
			# Recall thyself
			self.execute(query, args)

	def executefetch(self, query, args=None, cursor = None):
		log.debug("Execute Fetch Operation")
		log.debug("DB Query: %s" % query)
		log.debug("DB Values: %s" % args)

		try:
			# Ensure all is good
			self.check_connection()

			# Local cursor
			if cursor is None:
				cursor = self.MYSQL_CONNECTION.cursor(MySQLdb.cursors.DictCursor)

			# Run the SQL
			cursor.execute(query, args)
		except MySQLdb.OperationalError:
			log.warning("MySQL connection lost during ExecuteFetch.")
			self.reconnect()
			# Recall thyself
			cursor = self.executefetch(query, args, cursor)

		return cursor

	def executemany(self, query, args=None):
		log.debug("Execute Many Operation")
		try:
			# Ensure all is good
			self.check_connection()
			# Run the SQL
			self.MYSQL_CURSOR.executemany(query, args)
		except MySQLdb.OperationalError:
			log.warning("MySQL connection lost during Executemany.")
			self.reconnect()
			# Recall thyself
			self.executemany(query, args)

# -------------------------- END MySQL Operational Functions ---------------------------------------

	def hash_pass(self, password):
		m = hashlib.sha1()
		m.update(password)
		m.update(self.salt)

		return m.hexdigest()

	def update_hash_rate_stats(self, averageOverTime):
		log.debug("Updating Hash Rate Stats")
		# Note: we are using transactions... so we can set the speed = 0 and it doesn't take affect until we are commited.
		self.execute(
			"""
			UPDATE `pool_worker`
			SET `speed` = 0, 
			  `alive` = 0
			"""
		);

		stime = '%.0f' % (time.time() - averageOverTime);

		self.execute(
			"""
			UPDATE `pool_worker` pw
			LEFT JOIN (
				SELECT `worker`, SUM(`difficulty`) * 4294967296 / %(average)s AS 'speed'
				FROM `shares`
				WHERE `time` > FROM_UNIXTIME(%(time)s)
				GROUP BY `worker`
			) AS leJoin
			ON leJoin.`worker` = pw.`id`
			SET pw.`alive` = 1, 
			  pw.`speed` = leJoin.`speed`
			WHERE pw.`id` = leJoin.`worker`
			""",
			{
				"time": stime,
				"average": int(averageOverTime) * 1000000
			}
		)

		self.execute(
			"""
			UPDATE `pool`
			SET `value` = (
				SELECT IFNULL(SUM(`speed`), 0)
				FROM `pool_worker`
				WHERE `alive` = 1
			)
			WHERE `parameter` = 'pool_speed'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def import_shares(self, data):
		# Data layout
		# 0: worker_name, 
		# 1: block_header, 
		# 2: block_hash, 
		# 3: difficulty, 
		# 4: timestamp, 
		# 5: is_valid, 
		# 6: ip, 
		# 7: self.block_height, 
		# 8: self.prev_hash,
		# 9: invalid_reason, 
		# 10: share_diff

		log.debug("Importing Shares")
		checkin_times = {}
		total_shares = 0
		best_diff = 0

		for k, v in enumerate(data):
			total_shares += v[3]

			if v[0] in checkin_times:
				if v[4] > checkin_times[v[0]]:
					checkin_times[v[0]]["time"] = v[4]
			else:
				checkin_times[v[0]] = {
					"time": v[4], 
					"shares": 0, 
					"rejects": 0
				}

			if v[5] == True:
				checkin_times[v[0]]["shares"] += v[3]
			else:
				checkin_times[v[0]]["rejects"] += v[3]

			if v[10] > best_diff:
				best_diff = v[10]

			self.execute(
				"""
				INSERT INTO `shares` 
				(time, rem_host, worker, our_result, upstream_result, 
				  reason, solution, block_num, prev_block_hash, 
				  useragent, difficulty) 
				VALUES
				(FROM_UNIXTIME(%(time)s), %(host)s, 
				  (SELECT `id` FROM `pool_worker` WHERE `username` = %(uname)s ORDER by `id` LIMIT 1), 
				  %(lres)s, 0, %(reason)s, %(solution)s, 
				  %(blocknum)s, %(hash)s, '', %(difficulty)s)
				""",
				{
					"time": v[4],
					"host": v[6],
					"uname": v[0],
					"lres": v[5],
					"solution": v[2],
					"reason": v[9],
					"blocknum": v[7],
					"hash": v[8],
					"difficulty": v[3]
				}
			)

		# Updating some stats
		self.execute(
			"""
			SELECT `parameter`, `value` 
			FROM `pool` 
			WHERE `parameter` = 'round_best_share'
			  OR `parameter` = 'round_shares'
			  OR `parameter` = 'bitcoin_difficulty'
			  OR `parameter` = 'round_progress'
			"""
		)

		current_parameters = {}

		for data in self.MYSQL_CURSOR.fetchall():
			current_parameters[data[0]] = data[1]

		round_best_share = float(current_parameters['round_best_share'])
		difficulty = float(current_parameters['bitcoin_difficulty'])
		round_shares = float(current_parameters['round_shares']) + total_shares

		updates = [
			{
				"param": "round_shares",
				"value": round_shares
			},
			{
				"param": "round_progress",
				"value": 0 if difficulty == 0 else (round_shares / difficulty) * 100
			}
		]

		if best_diff > round_best_share:
			updates.append({
				"param": "round_best_share",
				"value": best_diff
			})

		self.executemany(
			"""
			UPDATE `pool` 
			SET `value` = %(value)s
			WHERE `parameter` = %(param)s
			""",
			updates
		)

		for k, v in checkin_times.items():
			self.execute(
				"""
				UPDATE `pool_worker`
				SET `last_checkin` = FROM_UNIXTIME(%(time)s), 
				  `total_shares` = `total_shares` + %(shares)s,
				  `total_rejects` = `total_rejects` + %(rejects)s
				WHERE `username` = %(uname)s
				""",
				{
					"time": v["time"],
					"shares": v["shares"],
					"rejects": v["rejects"], 
					"uname": k
				}
			)

		self.MYSQL_CONNECTION.commit()

	def found_block(self, data):
		# Note: difficulty = -1 here
		self.execute(
			"""
			UPDATE `shares`
			SET `upstream_result` = %(result)s,
			  `solution` = %(solution)s
			WHERE `time` = FROM_UNIXTIME(%(time)s)
			  AND `worker` = (
				  SELECT `id` 
				  FROM `pool_worker` 
				  WHERE `username` = %(uname)s
			  )
			LIMIT 1
			""",
			{
				"result": data[5], 
				"solution": data[2], 
				"time": data[4], 
				"uname": data[0]
			}
		)
		
		if self.database_extend and data[5] == True:
			self.execute(
				"""
				UPDATE `pool_worker`
				SET `total_found` = `total_found` + 1
				WHERE `username` = %(uname)s
				""",
				{
					"uname": data[0]
				}
			)
			self.execute(
				"""
				SELECT `value`
				FROM `pool`
				WHERE `parameter` = 'pool_total_found'
				"""
			)
			total_found = int(self.MYSQL_CURSOR.fetchone()[0]) + 1
			
			self.executemany(
				"""
				UPDATE `pool`
				SET `value` = %(value)s
				WHERE `parameter` = %(param)s
				""",
				[
					{
						"param": "round_shares",
						"value": "0"
					},
					{
						"param": "round_progress",
						"value": "0"
					},
					{
						"param": "round_best_share",
						"value": "0"
					},
					{
						"param": "round_start",
						"value": time.time()
					},
					{
						"param": "pool_total_found",
						"value": total_found
					}
				]
			)

		self.MYSQL_CONNECTION.commit()

	def list_users(self):
		result = self.executefetch(
			"""
			SELECT *
			FROM `pool_worker`
			WHERE `id`> 0
			"""
		)
		
		while True:
			results = result.fetchmany()
			if not results:
				break

			for result in results:
				yield result

		result.close()

	def get_user(self, id_or_username):
		log.debug("Finding user with id or username of %s", id_or_username)

		result = self.executefetch(
			"""
			SELECT *
			FROM `pool_worker`
			WHERE `id` = %(id)s
			  OR `username` = %(uname)s
			""",
			{
				"id": id_or_username if id_or_username.isdigit() else -1,
				"uname": id_or_username
			}
		)

		user = result.fetchone()
		result.close()
		return user

	def get_user_settings(self, worker_id):
		log.debug("Finding configuration with worker_id of %s", worker_id)

		result = self.executefetch(
			"""
			SELECT *
			FROM `pool_worker_settings`
			WHERE `pool_worker_id` = %(id)s
			""",
			{
				"id": worker_id
			}
		)

		user_settings = result.fetchone()
		result.close()
		return user_settings

	def delete_user(self, id_or_username):
		if id_or_username.isdigit() and id_or_username == '0':
			raise Exception('You cannot delete that user')
		
		log.debug("Deleting user with id or username of %s", id_or_username)
		
		self.execute(
			"""
			UPDATE `shares`
			SET `worker` = 0
			WHERE `worker` = (
				SELECT `id` 
				FROM `pool_worker` 
				WHERE `id` = %(id)s 
				  OR `username` = %(uname)s
				LIMIT 1
			)
			""",
			{
				"id": id_or_username if id_or_username.isdigit() else -1,
				"uname": id_or_username
			}
		)

		self.execute(
			"""
			DELETE FROM `pool_worker`
			WHERE `id` = %(id)s
			  OR `username` = %(uname)s
			""", 
			{
				"id": id_or_username if id_or_username.isdigit() else -1,
				"uname": id_or_username
			}
		)

		self.MYSQL_CONNECTION.commit()

	def insert_user(self, username, password):
		log.debug("Adding new user %s", username)
		
		self.execute(
			"""
			INSERT INTO `pool_worker`
			(`username`, `password`)
			VALUES
			(%(uname)s, %(pass)s)
			""",
			{
				"uname": username, 
				"pass": self.hash_pass(password)
			}
		)

		self.MYSQL_CONNECTION.commit()

		return str(username)

	def update_user(self, id_or_username, password):
		log.debug("Updating password for user %s", id_or_username);
		
		self.execute(
			"""
			UPDATE `pool_worker`
			SET `password` = %(pass)s
			WHERE `id` = %(id)s
			  OR `username` = %(uname)s
			""",
			{
				"id": id_or_username if id_or_username.isdigit() else -1,
				"uname": id_or_username,
				"pass": self.hash_pass(password)
			}
		)
		
		self.MYSQL_CONNECTION.commit()

	def update_worker_diff(self, username, diff):
		log.debug("Setting difficulty for %s to %s", username, diff)

		self.execute(
			"""
			UPDATE `pool_worker`
			SET `difficulty` = %(diff)s
			WHERE `username` = %(uname)s
			""",
			{
				"uname": username, 
				"diff": diff
			}
		)

		self.MYSQL_CONNECTION.commit()

	def clear_worker_diff(self):
		if self.database_extend:
			log.debug("Resetting difficulty for all workers")

			self.execute(
				"""
				UPDATE `pool_worker`
				SET `difficulty` = 0
				"""
			)

			self.MYSQL_CONNECTION.commit()

	def check_password(self, username, password):
		log.debug("Checking username/password for %s", username)

		self.execute(
			"""
			SELECT COUNT(*) 
			FROM `pool_worker`
			WHERE `username` = %(uname)s
			  AND `password` = %(pass)s
			""",
			{
				"uname": username, 
				"pass": self.hash_pass(password)
			}
		)

		data = self.MYSQL_CURSOR.fetchone()

		if data[0] > 0:
			return True

		return False

	def update_pool_info(self, pi):
		self.executemany(
			"""
			UPDATE `pool`
			SET `value` = %(value)s
			WHERE `parameter` = %(param)s
			""",
			[
				{
					"param": "bitcoin_blocks",
					"value": pi['blocks']
				},
				{
					"param": "bitcoin_balance",
					"value": pi['balance']
				},
				{
					"param": "bitcoin_connections",
					"value": pi['connections']
				},
				{
					"param": "bitcoin_difficulty",
					"value": pi['difficulty']
				},
				{
					"param": "bitcoin_infotime",
					"value": time.time()
				}
			]
		)

		self.MYSQL_CONNECTION.commit()

	def get_worker_diff(self,username):
		# Defualt Value
		worker_diff = settings.POOL_TARGET

		#Load from database
		self.MYSQL_CURSOR.execute("SELECT difficulty FROM pool_worker WHERE username = %s",(username))
		data = self.MYSQL_CURSOR.fetchone()

		#Check result
		if data[0] > 0 :
			worker_diff = data[0]

		# All done!
		return worker_diff;

	def set_worker_diff(self,username, difficulty):
		self.execute("UPDATE `pool_worker` SET `difficulty` = %s WHERE `username` = %s",(difficulty,username))
		self.MYSQL_CONNECTION.commit()

	def check_tables(self):
		log.debug("Checking Tables")

		self.execute(
			"""
			SELECT COUNT(*)
			FROM INFORMATION_SCHEMA.STATISTICS
			WHERE `table_schema` = %(schema)s
			  AND `table_name` = 'shares'
			""",
			{
				"schema": getattr(settings, 'DB_MYSQL_DBNAME')
			}
		)

		data = self.MYSQL_CURSOR.fetchone()

		if data[0] <= 0:
			self.update_version_1()		# no, we don't, so create them

		if self.database_extend:
			self.update_tables()

	def update_tables(self):
		version = 0
		current_version = 10

		while version < current_version:
			self.execute(
				"""
				SELECT `value`
				FROM `pool`
				WHERE parameter = 'DB Version'
				"""
			)

			data = self.MYSQL_CURSOR.fetchone()
			version = int(data[0])

			if version < current_version:
				log.info("Updating Database from %i to %i" % (version, version +1))
				getattr(self, 'update_version_' + str(version) )()

	def update_version_1(self):
		if self.database_extend:
			self.execute(
				"""
				CREATE TABLE IF NOT EXISTS `shares`
				(
					`id` SERIAL PRIMARY KEY,
					`time` TIMESTAMP,
					`rem_host` TEXT,
					`username` TEXT,
					`our_result` BOOLEAN,
					`upstream_result` BOOLEAN,
					`reason` TEXT,
					`solution` TEXT,
					`block_num` INTEGER,
					`prev_block_hash` TEXT,
					`useragent` TEXT,
					`difficulty` INTEGER
				)
				ENGINE=MYISAM
				"""
			)

			self.execute(
				"""
				CREATE INDEX `shares_username` ON `shares`(`username`(10))
				"""
			)

			self.execute(
				"""
				CREATE TABLE IF NOT EXISTS `pool_worker`
				(
					`id` SERIAL PRIMARY KEY,
					`username` TEXT,
					`password` TEXT,
					`speed` INTEGER,
					`last_checkin` TIMESTAMP
				)
				ENGINE=MYISAM
				"""
			)

			self.execute(
				"""
				CREATE INDEX `pool_worker_username` ON `pool_worker`(`username`(10))
				"""
			)

			self.execute(
				"""
				CREATE TABLE IF NOT EXISTS `pool`
				(
					`parameter` TEXT,
					`value` TEXT
				)
				"""
			)

			self.execute(
				"""
				ALTER TABLE `pool_worker` ADD `total_shares` INTEGER DEFAULT 0
				"""
			)

			self.execute(
				"""
				ALTER TABLE `pool_worker` ADD `total_rejects` INTEGER DEFAULT 0
				"""
			)

			self.execute(
				"""
				ALTER TABLE `pool_worker` ADD `total_found` INTEGER DEFAULT 0
				"""
			)

			self.execute(
				"""
				INSERT INTO `pool`
				(parameter, value)
				VALUES
				('DB Version', 2)
				"""
			)
		else:
			self.execute(
				"""
				CREATE TABLE IF NOT EXISTS `shares`
				(
					`id` SERIAL,
					`time` TIMESTAMP,
					`rem_host` TEXT,
					`username` TEXT,
					`our_result` INTEGER,
					`upstream_result` INTEGER,
					`reason` TEXT,
					`solution` TEXT
				)
				ENGINE=MYISAM
				"""
			)

			self.execute(
				"""
				CREATE INDEX `shares_username` ON `shares`(`username`(10))
				"""
			)

			self.execute(
				"""
				CREATE TABLE IF NOT EXISTS `pool_worker`
				(
					`id` SERIAL,
					`username` TEXT, 
					`password` TEXT
				)
				ENGINE=MYISAM
				"""
			)

			self.execute(
				"""
				CREATE INDEX `pool_worker_username` ON `pool_worker`(`username`(10))
				"""
			)

		self.MYSQL_CONNECTION.commit()


	def update_version_2(self):
		log.info("running update 2")

		self.executemany(
			"""
			INSERT INTO `pool` (`parameter`, `value`) VALUES (%s, %s)
			""",
			[
				('bitcoin_blocks', 0),
				('bitcoin_balance', 0),
				('bitcoin_connections', 0),
				('bitcoin_difficulty', 0),
				('pool_speed', 0),
				('pool_total_found', 0),
				('round_shares', 0),
				('round_progress', 0),
				('round_start', time.time())
			]
		)

		self.execute(
			"""
			UPDATE `pool`
			SET `value` = 3
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_3(self):
		log.info("running update 3")

		self.executemany(
			"""
			INSERT INTO `pool` (`parameter`, `value`) VALUES (%s, %s)
			""",
			[
				('round_best_share', 0),
				('bitcoin_infotime', 0)
			]
		)

		self.execute(
			 """
			 ALTER TABLE `pool_worker` ADD `alive` BOOLEAN
			 """
		)

		self.execute(
			"""
			UPDATE `pool`
			SET `value` = 4
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_4(self):
		log.info("running update 4")

		self.execute(
			"""
			ALTER TABLE `pool_worker`
			ADD `difficulty` INTEGER DEFAULT 0
			"""
		)

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS `shares_archive`
			(
				`id` SERIAL PRIMARY KEY,
				`time` TIMESTAMP,
				`rem_host` TEXT,
				`username` TEXT,
				`our_result` BOOLEAN,
				`upstream_result` BOOLEAN,
				`reason` TEXT,
				`solution` TEXT,
				`block_num` INTEGER,
				`prev_block_hash` TEXT,
				`useragent` TEXT,
				`difficulty` INTEGER
			)
			ENGINE = MYISAM
			"""
		)

		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS `shares_archive_found`
			(
				`id` SERIAL PRIMARY KEY,
				`time` TIMESTAMP,
				`rem_host` TEXT,
				`username` TEXT,
				`our_result` BOOLEAN,
				`upstream_result` BOOLEAN,
				`reason` TEXT,
				`solution` TEXT,
				`block_num` INTEGER,
				`prev_block_hash` TEXT,
				`useragent` TEXT,
				`difficulty` INTEGER
			)
			ENGINE = MYISAM
			"""
		)

		self.execute(
			"""
			UPDATE `pool`
			SET `value` = 5
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_5(self):
		log.info("running update 5")

		self.execute(
			"""
			ALTER TABLE `pool`
			ADD PRIMARY KEY (`parameter`(100))
			"""
		)

		# Adjusting indicies on table: shares
		self.execute(
			"""
			DROP INDEX `shares_username` ON `shares`
			"""
		)

		self.execute(
			"""
			CREATE INDEX `shares_time_username` ON `shares`(`time`, `username`(10))
			"""
		)

		self.execute(
			"""
			CREATE INDEX `shares_upstreamresult` ON `shares`(`upstream_result`)
			"""
		)

		self.execute(
			"""
			UPDATE `pool`
			SET `value` = 6
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_6(self):
		log.info("running update 6")

		self.execute(
			"""
			ALTER TABLE `pool`
			CHARACTER SET = utf8,
			COLLATE = utf8_general_ci,
			ENGINE = InnoDB,
			CHANGE COLUMN `parameter` `parameter` VARCHAR(128) CHARACTER SET 'utf8' COLLATE 'utf8_general_ci' NOT NULL,
			CHANGE COLUMN `value` `value` VARCHAR(512) CHARACTER SET 'utf8' COLLATE 'utf8_general_ci' NULL,
			DROP PRIMARY KEY, ADD PRIMARY KEY (`parameter`)
			"""
		)

		self.execute(
			"""
			UPDATE `pool_worker`
			SET `password` = SHA1(CONCAT(password, %(salt)s))
			WHERE id > 0
			""",
			{
				"salt": self.salt
			}
		)

		self.execute(
			"""
			ALTER TABLE `pool_worker`
			CHARACTER SET = utf8,
			COLLATE = utf8_general_ci,
			ENGINE = InnoDB,
			CHANGE COLUMN `username` `username` VARCHAR(512) CHARACTER SET 'utf8' COLLATE 'utf8_general_ci' NOT NULL,
			CHANGE COLUMN `password` `password` CHAR(40) CHARACTER SET 'utf8' COLLATE 'utf8_bin' NOT NULL,
			CHANGE COLUMN `speed` `speed` INT(10) UNSIGNED NOT NULL DEFAULT '0',
			CHANGE COLUMN `total_shares` `total_shares` INT(10) UNSIGNED NOT NULL DEFAULT '0',
			CHANGE COLUMN `total_rejects` `total_rejects` INT(10) UNSIGNED NOT NULL DEFAULT '0',
			CHANGE COLUMN `total_found` `total_found` INT(10) UNSIGNED NOT NULL DEFAULT '0',
			CHANGE COLUMN `alive` `alive` TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
			CHANGE COLUMN `difficulty` `difficulty` INT(10) UNSIGNED NOT NULL DEFAULT '0',
			ADD UNIQUE INDEX `pool_worker-username` (`username`(128) ASC),
			ADD INDEX `pool_worker-alive` (`alive`),
			DROP INDEX `pool_worker_username`,
			DROP INDEX `id`
			"""
		)

		self.execute(
			"""
			ALTER TABLE `shares`
			ADD COLUMN `worker` BIGINT(20) UNSIGNED NOT NULL DEFAULT 0 AFTER `username`,
			DROP INDEX `id`,
			ENGINE = InnoDB;
			"""
		)

		self.execute(
			"""
			UPDATE `shares`
			JOIN `pool_worker`
			  ON `pool_worker`.`username` = `shares`.`username`
			SET `worker` = `pool_worker`.`id`
			"""
		)

		self.execute(
			"""
			SET SESSION sql_mode='NO_AUTO_VALUE_ON_ZERO';
			"""
		)

		self.execute(
			"""
			INSERT INTO `pool_worker`
			(`id`, `username`, `password`)
			VALUES
			(0, SHA1(RAND(CURRENT_TIMESTAMP)), SHA1(CURRENT_TIMESTAMP))
			"""
		)

		self.execute(
			"""
			SET SESSION sql_mode='';
			"""
		)

		self.execute(
			"""
			ALTER TABLE `shares` 
			  ADD CONSTRAINT `workerid`
			  FOREIGN KEY (`worker` )
			  REFERENCES `pool_worker` (`id`)
			  ON DELETE NO ACTION
			  ON UPDATE NO ACTION,
			DROP INDEX `shares_time_username`,
			ADD INDEX `shares_time_worker` (`time` ASC, `worker` ASC),
			ADD INDEX `shares_worker` (`worker` ASC),
			DROP COLUMN `username`
			"""
		)

		self.execute(
			"""
			UPDATE `pool` 
			SET `value` = 7
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_7(self):
		log.info("running update 7")
		self.execute(
			"""
			CREATE TABLE IF NOT EXISTS `payments` (
			`id` int(11) NOT NULL AUTO_INCREMENT,
			`solution` varchar(80) NOT NULL,
			`pstatus` varchar(50) NOT NULL DEFAULT 'pending',
			`txid` text,
			`amount` int(11) NOT NULL DEFAULT '0',
			`last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
			PRIMARY KEY (`id`),
			UNIQUE KEY `solution` (`solution`)
			) ENGINE=MyISAM DEFAULT CHARSET=latin1;
			"""
		)

		self.execute(
			"""
			UPDATE `pool` 
			SET `value` = 8
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_8(self):
		# Change difficulty column to float
		log.info("running update 8")
		self.execute(
			"""
			ALTER TABLE `shares`
			CHANGE COLUMN `difficulty` `difficulty` 
			FLOAT UNSIGNED NULL DEFAULT NULL;
			"""
		)

		self.execute(
			"""
			ALTER TABLE `pool_worker`
			CHANGE COLUMN `difficulty` `difficulty` 
			FLOAT UNSIGNED NOT NULL DEFAULT '0';
			"""
		)

		self.execute(
			"""
			UPDATE `pool` 
			SET `value` = 9
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()

	def update_version_9(self):
		# Add a pool_worker_settings table
		log.info("running update 9")
		self.execute(
			"""
			CREATE TABLE `pool_worker_settings` (
				`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
				`pool_worker_id` INT(10) UNSIGNED NOT NULL DEFAULT '0',
				`custom_diff_enable` TINYINT(3) UNSIGNED NOT NULL DEFAULT '0',
				PRIMARY KEY (`id`),
				UNIQUE INDEX `pool_worker_id` (`pool_worker_id`)
			)
			COLLATE='latin1_swedish_ci'
			ENGINE=MyISAM
			;
			"""
		)

		self.execute(
			"""
			UPDATE `pool` 
			SET `value` = 10
			WHERE `parameter` = 'DB Version'
			"""
		)

		self.MYSQL_CONNECTION.commit()