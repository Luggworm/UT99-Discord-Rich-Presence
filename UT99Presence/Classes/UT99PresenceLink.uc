class UT99PresenceLink extends UdpLink;

var IpAddr Destination;
var int MatchToken;

function PostBeginPlay()
{
    Super.PostBeginPlay();
    if (!StringToIpAddr("127.0.0.1", Destination))
    {
        Log("UT99Presence: could not parse loopback address");
        Destroy();
        return;
    }
    Destination.Port = 29777;
    MatchToken = Rand(2147483647);
    BindPort();
    SetTimer(3.0, true);
    SendStatus();
}

function Timer()
{
    SendStatus();
}

function SendStatus()
{
    local string MapName, GameMode;
    local Pawn P;
    local int Humans, Bots;
    local PlayerPawn LocalPlayer;
    local string CharacterName, CharacterClass, FaceTexture;
    local int Frags, Deaths, FragLimit, ObjectiveLimit;
    local string ObjectiveKind;
    FragLimit = 0;
    if (DeathMatchPlus(Level.Game) != None)
        FragLimit = DeathMatchPlus(Level.Game).FragLimit;
    ObjectiveLimit = 0;
    ObjectiveKind = "";
    if (CTFGame(Level.Game) != None)
    {
        ObjectiveLimit = int(CTFGame(Level.Game).GoalTeamScore);
        ObjectiveKind = "Capture Limit";
    }
    else if (Domination(Level.Game) != None)
    {
        ObjectiveLimit = int(Domination(Level.Game).GoalTeamScore);
        ObjectiveKind = "Score Limit";
    }
    else if (Assault(Level.Game) != None)
    {
        ObjectiveLimit = Assault(Level.Game).TimeLimit;
        ObjectiveKind = "Time Limit";
    }
    else if (TeamGamePlus(Level.Game) != None)
    {
        ObjectiveLimit = int(TeamGamePlus(Level.Game).GoalTeamScore);
        ObjectiveKind = "Score Limit";
    }
    else if (FragLimit > 0)
    {
        ObjectiveLimit = FragLimit;
        ObjectiveKind = "Frag Limit";
    }
    MapName = string(Level.Outer.Name);
    if (Level.Game != None)
        GameMode = string(Level.Game.Class);
    // Count active players, not spectators or waiting players.
    // Bot is the UT99 Bot class; other active PlayerPawns are humans.
    Humans = 0;
    Bots = 0;
    foreach AllActors(class'Pawn', P)
    {
        if (P.PlayerReplicationInfo == None)
            continue;
        if (P.PlayerReplicationInfo.bIsSpectator || P.PlayerReplicationInfo.bWaitingPlayer)
            continue;
        if (P.IsA('Bot'))
            Bots++;
        else if (P.IsA('PlayerPawn'))
            Humans++;
    }
    CharacterName = "";
    CharacterClass = "";
    Frags = 0;
    Deaths = 0;
    foreach AllActors(class'PlayerPawn', LocalPlayer)
    {
        if (LocalPlayer.PlayerReplicationInfo == None)
            continue;
        CharacterName = LocalPlayer.PlayerReplicationInfo.PlayerName;
        CharacterClass = string(LocalPlayer.Class);
        // MultiSkins[3] is the conventional UT99 player face texture slot.
        if (LocalPlayer.MultiSkins[3] != None)
            FaceTexture = string(LocalPlayer.MultiSkins[3]);
        Frags = int(LocalPlayer.PlayerReplicationInfo.Score);
        Deaths = int(LocalPlayer.PlayerReplicationInfo.Deaths);
        break;
    }
    SendText(Destination, "UT99|" $ MapName $ "|" $ GameMode $ "|" $ string(MatchToken) $ "|" $ string(Humans) $ "|" $ string(Bots) $ "|" $ CharacterName $ "|" $ CharacterClass $ "|" $ string(Frags) $ "|" $ string(Deaths) $ "|" $ FaceTexture $ "|" $ string(FragLimit) $ "|" $ string(ObjectiveLimit) $ "|" $ ObjectiveKind);
}

defaultproperties
{
    RemoteRole=ROLE_None
}
