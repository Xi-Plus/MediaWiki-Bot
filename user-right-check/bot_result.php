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

$timelimit = date("Y-m-d H:i:s", mktime(date("H"), date("i"), date("s"), date("n"), date("j"), date("Y")-2));
echo "顯示最後動作 < ".$timelimit."<br>";

if (isset($_POST["owner"])) {
	$time = strtotime($_POST["time"]);
	if ($time === false) {
		echo "更新".$_POST["owner"]."的最後編輯時間失敗<br>";
	} else {
		$time = date("Y-m-d H:i:s", $time);
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `userlastedit` = :userlastedit WHERE `username` = :username");
		$sth->bindValue(":userlastedit", $time);
		$sth->bindValue(":username", $_POST["owner"]);
		$sth->execute();
		WriteLog("update user ".$_POST["owner"]." lastedit = ".$time);
		echo "成功更新".$_POST["owner"]."的最後編輯時間為".$time."<br>";
	}
}

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `botlastedit` < :botlastedit AND `botlastlog` < :botlastlog AND `userlastedit` < :userlastedit AND `userlastlog` < :userlastlog ORDER BY `botlastedit` ASC, `botlastlog` ASC, `userlastedit` ASC, `userlastlog` ASC");
$sth->bindValue(":botlastedit", $timelimit);
$sth->bindValue(":botlastlog", $timelimit);
$sth->bindValue(":userlastedit", $timelimit);
$sth->bindValue(":userlastlog", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$count = 1;
?>
<table>
<tr>
	<th>#</th>
	<th>bot</th>
	<th>bot last edit</th>
	<th>bot last log</th>
	<th>owner</th>
	<th>owner last edit</th>
	<th>owner last log</th>
</tr>
<?php
foreach ($row as $bot) {
	?><tr>
		<td><?php echo ($count++); ?></td>
		<td><a href="https://zh.wikipedia.org/wiki/User:<?=$bot["botname"]?>" target="_blank"><?=$bot["botname"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:用户贡献/<?=$bot["botname"]?>" target="_blank"><?=$bot["botlastedit"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:日志/<?=$bot["botname"]?>" target="_blank"><?=$bot["botlastlog"]?></a></td>
		<td><a href="https://zh.wikipedia.org/wiki/User:<?=$bot["username"]?>" target="_blank"><?=$bot["username"]?></a></td>
		<td>
			<form method="post" style="margin: 0px;">
				<a href="https://zh.wikipedia.org/wiki/Special:用户贡献/<?=$bot["username"]?>" target="_blank"><?=$bot["userlastedit"]?></a>
				<a href="https://tools.wmflabs.org/guc/?by=date&user=<?=$bot["username"]?>" target="_blank">全域貢獻</a>
				<input type="text" name="time">
				<input type="hidden" name="owner" value="<?=$bot["username"]?>">
			</form>
		</td>
		<td><a href="https://zh.wikipedia.org/wiki/Special:日志/<?=$bot["username"]?>" target="_blank"><?=$bot["userlastlog"]?></a></td>
	</tr><?php
}
?>
</table>
</body>
</html>
