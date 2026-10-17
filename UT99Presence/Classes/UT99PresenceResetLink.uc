class UT99PresenceResetLink extends UdpLink;

var IpAddr Destination;

function PostBeginPlay()
{
    Super.PostBeginPlay();
    if (!StringToIpAddr("127.0.0.1", Destination))
    {
        Destroy();
        return;
    }
    Destination.Port = 29777;
    BindPort();
    SendText(Destination, "UT99|RESET");
    Log("UT99Presence: reset command sent");
    Destroy();
}

defaultproperties
{
    RemoteRole=ROLE_None
}
