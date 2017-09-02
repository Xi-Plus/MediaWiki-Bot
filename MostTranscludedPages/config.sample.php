<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C["TIME_MIN"] = "1970-01-01 08:00:01";
$C["protection_update"] = "-7 days";

$C["User-Agent"] = "User:A2093064-bot MostTranscludedPages";

$C["DBTBprefix"] = "MostTranscludedPages_";

$C["cookiefile"] = __DIR__."/../tmp/MostTranscludedPages-cookie.txt";

$C["fail_retry"] = 5;

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
