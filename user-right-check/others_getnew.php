<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");
require(__DIR__."/../function/log.php");
require(__DIR__."/function.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

// get user list from database
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
foreach ($row as $user) {
	$user["rights"] = explode("|", $user["rights"]);
	$userlist[$user["name"]] = $user;
}

// query user list
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "allusers",
	"augroup" => "sysop|bureaucrat|checkuser|oversight|ipblock-exempt|rollbacker|patroller|autoreviewer|confirmed",
	"auprop" => "groups",
	"aulimit" => "max"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$allusers = $res["query"]["allusers"];

$newuserlist = [];
foreach ($allusers as $user) {
	$newuserlist[$user["name"]] = $user["groups"];
}
$res = file_get_contents($C["AWBpage"]);
if ($res === false) {
	exit("fetch page fail\n");
}
$s = strpos($res, "<!--enabledusersbegins-->");
$e = strpos($res, "<!--enabledusersends-->");
$res = substr($res, $s, $e-$s);
if (preg_match_all("/^\* *([^ \n]+) *$/m", $res, $m)) {
	foreach ($m[1] as $key => $value) {
		if (!isset($newuserlist[$value])) {
			$newuserlist[$value] = userright($value, false);
		}
		$newuserlist[$value] []= $C["AWBright"];
	}
}
echo "result count: ".count($newuserlist)."\n";

$count = 0;
foreach ($newuserlist as $name => $rights) {
	$count++;
	sort($rights);
	if (!isset($userlist[$name])) {
		echo $count." ".$name."\n";
		$lastedit = lastedit($name);
		$lastlog = lastlog($name);
		$lastusergetrights = lastusergetrights($name);

		echo "lastedit: ".$lastedit."\n";
		echo "lastlog: ".$lastlog."\n";
		echo "lastusergetrights: ".$lastusergetrights."\n";

		$rights = implode("|", $rights);
		echo "rights: ".$rights."\n";

		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}userlist` (`name`, `lastedit`, `lastlog`, `lastusergetrights`, `rights`) VALUES (:name, :lastedit, :lastlog, :lastusergetrights, :rights)");
		$sth->bindValue(":name", $name);
		$sth->bindValue(":lastedit", $lastedit);
		$sth->bindValue(":lastlog", $lastlog);
		$sth->bindValue(":lastusergetrights", $lastusergetrights);
		$sth->bindValue(":rights", $rights);
		$res = $sth->execute();
		WriteLog("new user: ".$name." ".$rights);
		echo "\n";
	} else {
		$rights = implode("|", $rights);
		$userlist[$name]["rights"] = implode("|", $userlist[$name]["rights"]);
		if ($userlist[$name]["rights"] != $rights) {
			echo $count." ".$name."\n";
			echo $userlist[$name]["rights"]." -> ".$rights."\n";
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `rights` = :rights WHERE `name` = :name");
			$sth->bindValue(":name", $name);
			$sth->bindValue(":rights", $rights);
			$res = $sth->execute();
			WriteLog("update rights: ".$name." ".$userlist[$name]["rights"]."->".$rights);
		}
		unset($userlist[$name]);
	}
}

foreach ($userlist as $user) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}userlist` WHERE `name` = :name");
	$sth->bindValue(":name", $user["name"]);
	$res = $sth->execute();
	echo "remove ".$user["name"]." (".implode("|", $user["rights"]).")\n";
	WriteLog("remove user: ".$user["name"]);
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
