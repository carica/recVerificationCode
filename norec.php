<?php
namespace Carica\AutoSign;

require 'vendor/autoload.php';

use GuzzleHttp\Client;

class PHPWind75
{

    protected $site=[];
    /**
     * get site info from site.info file with each line represents one parameter in the following order:
     * 1: site url
     * 2: site username
     * 3: site password
     * 4: your token for telegram bot private message[http://t.me/privatemessenger_bot] (optional)
     */
    function getSiteInfo()
    {
        $filename = 'site.info';
        $handle = fopen($filename, 'r');
        $this->site['url'] = trim(fgets($handle));
        $this->site['username'] = trim(fgets($handle));
        $this->$site['password'] = trim(fgets($handle));
        if(!feof($handle)) {
            $this->site['botToken'] = trim(fgets($handle));
        }
        fclose($handle);
    }

    function sendTGmessage($result)
    {
        $botURL = 'bot_url';
        $post_bot = [
            'token' => $this->site['botToken'],
            'text' => $result,
        ];
        $bot_client = new Client();
        $r = $bot_client->request('POST', $botURL, ['form_params' => $post_bot]);
        print_r($r->getBody());
    }

    function run()
    {
        getSiteInfo();
        // print_r($site);
        $client = new Client([
            // Base URI is used with relative requests
            'base_uri' => $this->site['url'],
            // You can set any number of default request options.
            // 'timeout'  => 2.0,
            'cookies' => true,
            'headers' => [
                'User-Agent' => 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',

            ]
        ]);

        $response = $client->request('GET', '/login.php');
        $doc = new \DOMDocument();
        libxml_use_internal_errors(true);
        $doc->loadHTML($response->getBody());
        $inputs = $doc->getElementsByTagName('input');
        $post_data = [];
        foreach($inputs as $i) {
            $post_data[$i->getAttribute('name')]=$i->getAttribute('value');
        }
        $post_data['pwuser'] = $this->site['username'];
        $post_data['pwpwd'] = $this->site['password'];
        print_r($post_data);

        $i = 0;
        $logged = FALSE;
        do {
            $response = $client->request('POST', '/login.php', ['form_params' => $post_data]);
            //echo $response->getBody();
            $response = $client->request('GET', '/u.php');
            //echo $response->getBody();
            $pattern = '/var\s+verifyhash\s+=\s+\'(.*)\';/';
            preg_match($pattern, $response->getBody(), $matches);
            print_r($matches);
            $i++;
            if(count($matches) > 1) {
                $logged = TRUE;
            }
        } while((!$logged) && ($i < 3)); //try 3 times at most

        if(!$logged) {
            $result = 'logging error!';
        }
        else {
            $post_punch = [
                'action' => 'punch',
                'verify' => $matches[1],
                'step' => 2
            ];
            $response = $client->request('POST', '/jobcenter.php', ['form_params' => $post_punch]);
            $result = iconv('GBK', 'UTF-8', $response->getBody()); //phpwind 7.5 returns data encoded in GBK
        }
        //send message
        if(strlen($this->site['botToken']) > 0) {
            sendTGmessage($result);
        }
    }
}

$test = new PHPWind75();
$test->run();

