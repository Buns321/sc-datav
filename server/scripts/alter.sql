USE sc_datav;
ALTER TABLE enterprise_table CHANGE cnt `count` INT;
SELECT 'enterprise_table' AS t, `count` FROM enterprise_table;
