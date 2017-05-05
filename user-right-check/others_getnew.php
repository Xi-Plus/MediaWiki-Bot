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
	$userlist[$user["userid"]] = $user;
}

// query user list
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "allusers",
	"augroup" => "sysop|bureaucrat|checkuser|oversight|ipblock-exempt|rollbacker|patroller|autoreviewer|confirmed",
	"aulimit" => "max"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$allusers = $res["query"]["allusers"];
echo "result count: ".count($allusers)."\n";
$count = 1;
foreach ($allusers as $user) {
	echo ($count++)." ".$user["name"]." ".$user["userid"]."\n";
	if (!isset($userlist[$user["userid"]])) {
		$lastedit = lastedit($user["name"]);
		$lastlog = lastlog($user["name"]);
		$lastusergetrights = lastusergetrights($user["name"]);

		echo "lastedit: ".$lastedit."\n";
		echo "lastlog: ".$lastlog."\n";
		echo "lastusergetrights: ".$lastusergetrights."\n";

		$rights = implode("|", userright($user["name"]));
		echo "rights: ".$rights."\n";

		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}userlist` (`userid`, `name`, `lastedit`, `lastlog`, `lastusergetrights`, `rights`) VALUES (:userid, :name, :lastedit, :lastlog, :lastusergetrights, :rights)");
		$sth->bindValue(":userid", $user["userid"]);
		$sth->bindValue(":name", $user["name"]);
		$sth->bindValue(":lastedit", $lastedit);
		$sth->bindValue(":lastlog", $lastlog);
		$sth->bindValue(":lastusergetrights", $lastusergetrights);
		$sth->bindValue(":rights", $rights);
		$res = $sth->execute();
		WriteLog("new user: ".$user["name"]." ".$user["userid"]);
		echo "\n";
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
