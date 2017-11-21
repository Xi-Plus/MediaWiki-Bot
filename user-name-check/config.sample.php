<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C["limit"]["levenshtein"] = 3;
$C["limit"]["similar_text"] = 10;
$C["limit"]["similar_text_precent"] = 70;
$C["limit"]["count"] = 100;

$C["User-Agent"] = "User:A2093064-bot user-name-check";

$C["DBTBprefix"] = "ActiveUser";

$C["cookiefile"] = __DIR__."/../tmp/user-name-check-cookie.txt";

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
