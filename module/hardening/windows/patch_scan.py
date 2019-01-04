import os
import re

def get_patch_info_online():
    fp = os.popen('powershell "'+
        '$Session = New-Object -ComObject Microsoft.Update.Session;'+
        '$Searcher = $Session.CreateUpdateSearcher();'+
        '$updates=$Searcher.Search(\\"IsInstalled=1 or IsInstalled=0\\").Updates;'+
        'for($i=0;$i -lt $updates.Count;$i++){'+
        '    if($updates.Item($i).MsrcSeverity){'+
        '        echo \\"Title:\\"$updates.Item($i).Title;'+
        '        echo $updates.Item($i).IsInstalled;'+
        '        echo $updates.Item($i).MsrcSeverity;'+
        '        $collection=$updates.Item($i).KBArticleIDs;'+
        '        for($j=0;$j -lt $collection.Count;$j++){'+
        '            echo $collection.Item($j);'+
        '        }'+
        '    }'+
        '}"')
    info = fp.read()
    fp.close()
    infolist = info.split("Title:\n")[1:]
    is_installed = {}
    not_installed = {}
    for i in infolist:
        try:
            [title, isInstalled,MsrcSeverity,KB, empty] = i.split('\n')
            if isInstalled == "True":
                is_installed['KB'+KB] = (title,MsrcSeverity)
            else:
                not_installed['KB'+KB] = (title,MsrcSeverity)
        except:
            continue  # no KB number
    return not_installed


def get_patch_info_history():
    fp = os.popen(
        'powershell "$Session = New-Object -ComObject \\"Microsoft.Update.Session\\";' +
        '$Searcher = $Session.CreateUpdateSearcher();$' +
        'historyCount = $Searcher.GetTotalHistoryCount();' +
        '$result=$Searcher.QueryHistory(0, $historyCount);' +
        'for($i=0;$i -lt $result.Count;$i++){' +
        '   echo \\"Title:\\"$result.Item($i).Title;}"')
    info = fp.read()
    fp.close()
    infolist = info.split('Title:\n')[1:]
    is_installed = {}
    for i in infolist:
        match = re.search("KB\d{7}", i)
        if match:
            KB = match.group()
            is_installed[KB] = i.replace('\n', '')
    return is_installed


def run(payload, socket):
    response = {
        "cmd_id": payload["cmd_id"],
        "session_id": payload["args"]["session_id"],
        "patches": {},
        "error": ""
    }
    response['patches'] = get_patch_info_online()
    socket.response(response)
# $Session = New-Object -ComObject Microsoft.Update.Session;
# $Searcher = $Session.CreateUpdateSearcher();
# $updates=$Searcher.Search("IsInstalled=1 or IsInstalled=0").Updates;
# for($i=0;$i -lt $updates.Count;$i++){
#     if($updates.Item($i).MsrcSeverity){
#         echo "Title:"$updates.Item($i).Title;
#         echo $updates.Item($i).IsInstalled;
#         echo $updates.Item($i).MsrcSeverity;
#         $collection=$updates.Item($i).KBArticleIDs;
#         for($j=0;$j -lt $collection.Count;$j++){
#             echo $collection.Item($j);
#         }
#     }
# }

# $Session = New-Object - ComObject "Microsoft.Update.Session";
# $Searcher = $Session.CreateUpdateSearcher();
# $historyCount = $Searcher.GetTotalHistoryCount();
# $result =$Searcher.QueryHistory(0, $historyCount);
# for($i=0;$i - lt $result.Count;$i++){
#     echo "Title:"$result.Item($i).Title;
# }
