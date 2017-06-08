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
require(__DIR__."/../function/log.php");

$timelimit = date("Y-m-d H:i:s", strtotime("-2 years"));
echo "顯示最後動作 < ".$timelimit."<br>";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `botlastedit` < :botlastedit AND `botlastlog` < :botlastlog AND `userlastedit` < :userlastedit AND `userlastlog` < :userlastlog AND `reported` = 0 ORDER BY `botlastedit` ASC, `botlastlog` ASC, `userlastedit` ASC, `userlastlog` ASC");
$sth->bindValue(":botlastedit", $timelimit);
$sth->bindValue(":botlastlog", $timelimit);
$sth->bindValue(":userlastedit", $timelimit);
$sth->bindValue(":userlastlog", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
echo "共有".count($row)."筆<br><br>";
$count = 1;

foreach ($row as $user) {
	?>
==[[User:<?=$user["botname"]?>|<?=$user["botname"]?>]]==<br>
*機器人：{{User-multi|user=<?=$user["botname"]?>|t|c|l|cr}}<br>
*操作者：{{User-multi|user=<?=$user["username"]?>|t|c|l|sul2}}<br>
*機器人最後活動時間：<?php
$lastaction = max($user["botlastedit"], $user["botlastlog"]);
if ($lastaction == "0000-00-00 00:00:00") {
	echo "從未有編輯或日誌動作";
} else {
	$time = strtotime($lastaction);
	echo date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
?><br>
*操作者最後活動時間：<?php
$lastaction = max($user["userlastedit"], $user["userlastlog"]);
if ($lastaction == "0000-00-00 00:00:00") {
	echo "從未編輯過";
} else {
	$time = strtotime($lastaction);
	echo date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
?><br>
*發出通知時間：~~~~~以前<br>
*提交的維基人及時間：~~~~<br><br>
<?php
}
?>
</body>
</html>
