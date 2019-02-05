<?php

$C["DBhost"] = 'localhost';
$C['DBname'] = 'DBname';
$C['DBuser'] = 'DBuser';
$C['DBpass'] = 'DBpass';
$C['DBTBprefix'] = '';
$G["db"] = new PDO('mysql:host=' . $C["DBhost"] . ';dbname=' . $C["DBname"] . ';charset=utf8', $C["DBuser"], $C["DBpass"]);

$C["wikiapi"] = "https://test2.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";
$C["cookiefile"] = __DIR__ . "/../tmp/main-cookie.txt";

$C["User-Agent"] = "User:A2093064-bot";

$C["allowsapi"] = array("cli");

$C["test"] = false;
$C["check"] = false;
