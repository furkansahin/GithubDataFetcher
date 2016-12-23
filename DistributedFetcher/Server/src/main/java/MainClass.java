
import com.hazelcast.core.*;

import java.util.IllegalFormatCodePointException;
import java.util.StringJoiner;
import java.util.Timer;
import java.util.TimerTask;

public class MainClass {

    public static int counter = 0;
    public static int level = 0;
    public static boolean quit = false;
    public static HazelcastInstance hzServer;
    public static IQueue<String> firstQueue;
    public static IQueue<String> secondQueue;
    public static IQueue<String> credentials;
    public static ILock myLock;
    public static String exitCode;
    public static String token;

    public static final int maxCounter = 20;
    public static final int desiredLevel = 2;

    public static void addUser (String username, String password) {
        credentials.add(username + "||" + password);
    }

    public static void increaseLevel (){

        if(level == desiredLevel) {
            firstQueue.clear();
            while (!hzServer.getClientService().getConnectedClients().isEmpty()) {
                System.out.println("Trying to shutdown clients:");
                firstQueue.add(exitCode);
            }
            quit = true;
            System.out.println("Progress complete.");
            hzServer.shutdown();
            return;
        }
        if (hzServer.getClientService().getConnectedClients().isEmpty()) {
            System.out.println("Process is interrupted with worker quit ");
            hzServer.shutdown();
            quit = true;
            return;
        }
        myLock.lock();

        firstQueue.addAll(secondQueue);
        secondQueue.clear();

        myLock.unlock();
        level++;
        System.out.println("Level is increased to " + level);
        counter = 0;
    }

    public static void progress() {
        Timer t = new Timer();

        t.schedule(new TimerTask() {
            @Override
            public void run() {
                counter++;
                System.out.println("Counting:" + counter);
                if(counter  > maxCounter) {
                    increaseLevel();
                }

                if(quit)
                    t.cancel();
            }
        },1000,1000);
    }
    public static void main (String[] args) {

        hzServer = Hazelcast.newHazelcastInstance();

        exitCode = "q!s@#$%s1";
        token = "5f1d4372437f6fc4f92f34e5d379872b31c699f2";

        IMap<String,String> myMap = hzServer.getMap("infoMap");
        myMap.put("exit", exitCode);
        myMap.put("token", token);

        credentials = hzServer.getQueue("Credentials");

        addUser("githubfetcher1","fetcher12");
        addUser("githubfetcher2","fetcher12");
        addUser("githubfetcher1","fetcher12");
        addUser("githubfetcher2","fetcher12");
        addUser("githubfetcher1","fetcher12");
        addUser("githubfetcher2","fetcher12");
        firstQueue = hzServer.getQueue("BreadthSearch");
        secondQueue = hzServer.getQueue("NewQueue");

        firstQueue.addItemListener(new ItemListener<String>() {
            @Override
            public void itemAdded(ItemEvent<String> itemEvent) {
                System.out.println(itemEvent.getItem() + " is added");
            }

            @Override
            public void itemRemoved(ItemEvent<String> itemEvent) {
                System.out.println(itemEvent.getItem() + " is removed");
                counter = 0;
            }
        },true);

        firstQueue.add("furkansahin");

        ISet<String> myset = hzServer.getSet("GraphSet");

        myLock = hzServer.getLock("QueueLock");
        myLock.forceUnlock();

        hzServer.getClientService().addClientListener(new ClientListener() {
            @Override
            public void clientConnected(Client client) {
                progress();
            }

            @Override
            public void clientDisconnected(Client client) {
                if (hzServer.getClientService().getConnectedClients().isEmpty())
                    counter = maxCounter + 1;
            }
        });
        System.out.println("Setup is done. ");

    }

}
