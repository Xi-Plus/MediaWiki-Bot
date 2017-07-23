<html>
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0" />
</head>
<body>
<?php
require(__DIR__."/../config/config.php");
date_default_timezone_set('UTC');
@include(__DIR__."/config.php");

$limit = 25;
if (isset($_GET["limit"]) && is_numeric($_GET["limit"])) {
	$limit = (int)$_GET["limit"];
}
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}log` ORDER BY `time` DESC LIMIT ".$limit);
$sth->execute();
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
?>
<style type="text/css">
td {
	padding: 3px;
}
</style>
<table>
<tr>
	<th>time</th>
	<th>log</th>
</tr>
<?php
foreach ($row as $log) {
	?><tr>
		<td><?=$log["time"]?></td>
		<td><?=$log["message"]?></td>
	</tr><?php
}
?>
</table>
</body>
</html>
