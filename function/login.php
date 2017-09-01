<?php
function login() {
	global $C;
	echo "login as ".$C["user"]."\n";
	$res = cURL($C["wikiapi"]."?action=query&assert=user&format=json");
	if ($res === false) {
		exit("fetch page error 1\n");
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		$post = array(
			"lgname" => $C["user"],
			"lgpassword" => $C["pass"]
		);
		$res = cURL($C["wikiapi"]."?action=login&format=json", $post);
		if ($res === false) {
			exit("fetch page error 2\n");
		}
		$res = json_decode($res, true);
		if ($res["login"]["result"] === "NeedToken"){
			$token = $res["login"]["token"];
			$post = array(
				"lgname" => $C["user"],
				"lgpassword" => $C["pass"],
				"lgtoken" => $res["login"]["token"]
			);
			$res = cURL($C["wikiapi"]."?action=login&format=json", $post);
			if ($res === false) {
				exit("fetch page error 3\n");
			}
			$res = json_decode($res, true);
			if($res["login"]["result"] === "Success") {
				echo "login success.\n";
			} else {
				var_dump($res);
				exit("login fail 1\n");
			}
		} else {
			var_dump($res);
			exit("login fail 2\n");
		}
	} else {
		echo "aleardy login\n";
	}
}
