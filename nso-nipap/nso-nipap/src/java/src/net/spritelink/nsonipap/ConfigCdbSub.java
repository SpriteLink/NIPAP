package net.spritelink.nsonipap;

import net.spritelink.nsonipap.namespaces.*;

import java.util.*;
import java.math.BigInteger;

import org.apache.log4j.Logger;

import com.tailf.conf.*;
import com.tailf.ncs.ApplicationComponent;
import com.tailf.cdb.*;
import com.tailf.maapi.*;
import com.tailf.ncs.annotations.*;
import com.tailf.navu.*;
import com.tailf.ncs.NcsMain;
import com.tailf.ncs.ns.Ncs;

import java.net.Socket;
import java.net.SocketException;
import java.net.InetAddress;
import java.net.URL;
import java.util.ArrayList;
import java.util.EnumSet;

import jnipap.*;

public class ConfigCdbSub implements ApplicationComponent {
    private static Logger LOGGER = Logger.getLogger(ConfigCdbSub.class);

    private CdbSubscription sub = null;
    private CdbSession wsess;

    public ConfigCdbSub() {
    }

    @Resource(type=ResourceType.CDB, scope=Scope.CONTEXT,
            qualifier="reactive-fm-loop-subscriber")
    private Cdb cdb;

    @Resource(type=ResourceType.CDB, scope=Scope.CONTEXT,
            qualifier="w-reactive-fm-loop")
    private Cdb wcdb;

    @Resource(type=ResourceType.MAAPI, scope=Scope.INSTANCE,
            qualifier="reactive-fm-m")
    private Maapi maapi;

  private int th = -1;

  private Connection nipapCon;

    public void init() {
        LOGGER.info("Starting the CDB Connection...");
        try {
            wsess = wcdb.startSession(CdbDBType.CDB_OPERATIONAL);
            //Start CDB session
            maapi.startUserSession("admin", InetAddress.getLocalHost(),"system",
                    new String[] {"admin"},
                    MaapiUserSessionFlag.PROTO_TCP);

          th = maapi.startTrans(Conf.DB_RUNNING, Conf.MODE_READ);

          sub = cdb.newSubscription();

          sub.subscribe(1, new nipap(), 
              "/services/" +
              nipap.prefix + "/" +
              nipap._from_pool_ + "/" +
              nipap._request_);

            // Tell CDB we are ready for notifications
            sub.subscribeDone();

        }
        catch (Exception e) {
            LOGGER.error("", e);
        }
    }

    protected void addPrefixFromPrefix(String path, Prefix parentPrefix, ConfKey prefixKey) throws Exception {

      LOGGER.info("Create, From prefix request, path = " + path);
      Prefix child_prefix = new Prefix();
      try {

        AddPrefixOptions child_opts = new AddPrefixOptions();
        child_opts.put("prefix_length", "32");

        child_prefix = getPrefixAttributes(th, maapi, path + "/" + nipap._from_prefix_request_ + prefixKey );
        child_prefix.type = "host";
        child_prefix.save(nipapCon, parentPrefix, child_opts);

      }catch (Exception e ) {
        LOGGER.error("Unable to get prefix from prefix" + e.getMessage(), e);
        writeError(path, e.getMessage());
        return;
      }
      //write response
      wsess.create(path + "/" + nipap._response_ + "/" + nipap._from_prefix_ + prefixKey);
      writeResponse(child_prefix, path + "/" + nipap._response_ + "/" + nipap._from_prefix_ + prefixKey);
    }


    protected Prefix getPrefixAttributes(int th, Maapi maapi_, String attributePath) throws Exception
    {
      Prefix p = new Prefix();

      if (maapi_.exists(th, attributePath + "/" + nipap._customer_id_)) {
        ConfValue rCustomer_id = maapi.getElem(th, attributePath + "/" + nipap._customer_id_);
        p.customer_id = String.valueOf(rCustomer_id);
      }
      if (maapi_.exists(th, attributePath + "/" + nipap._description_)) {
        ConfValue rDescription = maapi.getElem(th, attributePath + "/" + nipap._description_);
        p.description = String.valueOf(rDescription);
      }
      if (maapi.exists(th, attributePath + "/" + nipap._node_)) {
        ConfValue rNode = maapi.getElem(th, attributePath + "/" + nipap._node_);
        p.node = String.valueOf(rNode);
      }
      if (maapi_.exists(th, attributePath + "/" + nipap._order_id_)) {
        ConfValue rOrder_id = maapi.getElem(th, attributePath + "/" + nipap._customer_id_);
        p.order_id = String.valueOf(rOrder_id);
      }
      
      return p;
    }

    protected AddPrefixOptions getPrefixOptions (int th,  Maapi maapi_, String argumentPath) throws Exception { 
      AddPrefixOptions opts = new AddPrefixOptions();

      ConfEnumeration family = (ConfEnumeration)maapi_.getElem(
          th, argumentPath + "/" + nipap._family_);
      opts.put("family", family.getOrdinalValue());

      if (maapi_.exists(th, argumentPath + "/" + nipap._prefix_length_)) {
        ConfValue pfx_length = maapi_.getElem(th, argumentPath + "/" + nipap._prefix_length_);
        opts.put("prefix_length", String.valueOf(pfx_length));
      }

      return opts;
    }

    protected void writeResponse(Prefix p, String responsePath) throws ConfException, Exception {

      if (p.family == 4) {
        ConfIPv4Prefix prefixValue = new ConfIPv4Prefix(p.prefix);
        LOGGER.info("SET: " + responsePath + "/prefix -> " + prefixValue);
        wsess.setElem(prefixValue, responsePath + "/" + nipap._prefix_);
      } else if (p.family == 6) {

        ConfIPv6Prefix prefixValue = new ConfIPv6Prefix(p.prefix);
        LOGGER.info("SET: " + responsePath + "/prefix -> " + prefixValue);
        wsess.setElem(prefixValue, responsePath + "/" + nipap._prefix_);
      }

      ConfUInt64 prefixIdValue = new ConfUInt64(p.id);
      wsess.setElem(prefixIdValue, responsePath + "/" + nipap._prefix_id_);

      ConfBuf customerIdValue = new ConfBuf(p.customer_id);
      if(customerIdValue != null){
        wsess.setElem(customerIdValue, responsePath + "/" + nipap._customer_id_);
      }

      if(p.description != null){
        ConfBuf descriptionValue = new ConfBuf(p.description);
        wsess.setElem(descriptionValue, responsePath + "/" + nipap._description_);
      }

      if(p.node != null){
        ConfBuf nodeValue = new ConfBuf(p.node);
        wsess.setElem(nodeValue, responsePath + "/" + nipap._node_);
      }
      
      if(p.order_id != null){
        ConfBuf orderIdValue = new ConfBuf(p.order_id);
        wsess.setElem(orderIdValue, responsePath + "/" + nipap._order_id_);
      }
    }


    protected void writeError(String path, String errorMessage) throws Exception {

      wsess.setElem(new ConfBuf(errorMessage), path + "/" + nipap._response_ + "/" + nipap._error_);
      wsess.setCase(nipap._response_choice_, nipap._error_, path + "/" + nipap._response_);

    }

    protected void removeResponse(String responsePath) throws ConfException, Exception {
      //unset case

      LOGGER.info("remove response " + responsePath);
      try {
        wsess.delete(responsePath + "/" + nipap._prefix_);
        wsess.delete(responsePath + "/" + nipap._prefix_id_);
        wsess.delete(responsePath + "/" + nipap._customer_id_);
        wsess.delete(responsePath + "/" + nipap._description_);
        wsess.delete(responsePath + "/" + nipap._node_);
        wsess.delete(responsePath + "/" + nipap._order_id_);
      } catch (CdbException e ){
      }
    }

    protected void removeChildPrefix(String prefixPath) throws ConfException, Exception {

      removePrefix(prefixPath);
      LOGGER.info("delete path + " + prefixPath);
      wsess.delete(prefixPath);
    }

    protected void removePrefix(String prefixPath) throws ConfException, Exception {
      try {
          ConfUInt64 p_id = (ConfUInt64)wsess.getElem(prefixPath + "/" + nipap._prefix_id_);
          LOGGER.info("Removing prefix ID: " + p_id);
          Prefix p = Prefix.get(nipapCon, Integer.parseInt(String.valueOf(p_id)));
          p.remove(nipapCon);
      } catch (Exception e) {
          LOGGER.error("Unable to remove prefix from NIPAP: " + e.getMessage(),e);
      }
    }

    public void run() {
        LOGGER.info("Starting the CDB subscriber...");        
        try {

            while(true) {
                // Read the subscription socket for new events
                int[] points = null;
                try {
                    // Blocking call, will throw an exception on package reload/redeploy
                    points = sub.read();
                } catch (ConfException e) {
                    LOGGER.debug("Possible redeploy/reload of package, exiting");
                    return;
                }
                // DiffIterateFlags tell our DiffIterator implementation what values we want
                EnumSet<DiffIterateFlags> enumSet =
                        EnumSet.<DiffIterateFlags>of(
                                DiffIterateFlags.ITER_WANT_PREV,
                                DiffIterateFlags.ITER_WANT_ANCESTOR_DELETE,
                                DiffIterateFlags.ITER_WANT_SCHEMA_ORDER);
                ArrayList<Request> reqs = new ArrayList<Request>();
                try {
                    // Iterate through the diff tree using the Iter class
                    // reqs ArrayList is filled with requests for operations (create, delete)
                    sub.diffIterate(points[0],
                            new Iter(sub),
                            enumSet, reqs);
                }
                catch (Exception e) {
                    reqs = null;
                }

                // Loop through CREATE or DELETE requests
                for (Request req : reqs) {
                    LOGGER.debug("Requested NIPAP action, op=" + req.op + " , type=" + req.t);

          try {
            // TODO: make backend configurable (now it is 'default')
            ConfValue bHost = maapi.getElem(th, "/services/nipap/backend{default}/hostname");
            ConfValue bPort = maapi.getElem(th, "/services/nipap/backend{default}/port");
            ConfValue bUser = maapi.getElem(th, "/services/nipap/backend{default}/username");
            ConfValue bPass = maapi.getElem(th, "/services/nipap/backend{default}/password");

            URL url = new URL("http://" + String.valueOf(bHost) + ":" + String.valueOf(bPort) + "/RPC2");
            nipapCon = new Connection(url, String.valueOf(bUser), String.valueOf(bPass));
            nipapCon.authoritative_source = "ncs";

          } catch (Exception e) {
            LOGGER.error("Unable to initiate connection to NIPAP: " + e.getMessage());
            continue;
          }


          // allocate prefix
          if (req.op == Operation.ALLOCATE && req.t == Type.Request ) {

            LOGGER.info("Trying to allocate a prefix for: " + req.request_key + " from pool: " + req.pool_key);

            String poolName = String.valueOf(req.pool_key).replaceAll("[{}]", "");

            Prefix p = new Prefix();
            // Gather prefix data and perform NIPAP request
            try {
              // Pool
              HashMap<String, String> poolSpec = new HashMap<>();
              poolSpec.put("name", poolName);
              List poolRes = Pool.list(nipapCon, poolSpec);
              if(poolRes.size() < 1){
                writeError(req.path.toString(), "Nipap pool not found");
                continue;
              }

              // options, like address-family
              AddPrefixOptions opts = getPrefixOptions(th, maapi, req.path + "/" + nipap._arguments_);

              //set prefix attributes
              String attrPath = req.path + "/" + nipap._attributes_;
              p = getPrefixAttributes(th, maapi, attrPath);

              p.save(nipapCon, (Pool)poolRes.get(0), opts);

            } catch (Exception e) {
              LOGGER.error("Unable to get prefix from NIPAP: " + e.getMessage(), e);
              writeError(req.path.toString(), e.getMessage());
              continue;
            }

            // Write the result
            String resPath = req.path + "/" + nipap._response_ + "/" + nipap._from_pool_;
            writeResponse(p, resPath);
            //set case
            wsess.setCase(nipap._response_choice_, nipap._ok_, req.path + "/" + nipap._response_ );


            // Request prefix from prefix
            if(maapi.exists(th, req.path + "/" + nipap._from_prefix_request_)){
              MaapiCursor pfx_cur = maapi.newCursor(th, req.path + "/" + nipap._from_prefix_request_);
              ConfKey pfx = null;
              while((pfx = maapi.getNext(pfx_cur)) != null) {

                addPrefixFromPrefix(req.path.toString(), p, pfx);
              }
              
            }

            // Redeploy
            try {
              ConfValue redeployPath = maapi.getElem(th, req.path + "/redeploy-service");
              LOGGER.info("redeploy-service: " + redeployPath);
              redeploy(redeployPath.toString());
            } catch (Exception e) {
              LOGGER.error("Redeploy failed: " + e.getMessage());
              }
          }
          /*
           * Allocate from-prefix
           *
           */
          else if (req.op == Operation.ALLOCATE && req.t == Type.FromPrefixRequest){
            LOGGER.info("Create, From prefix request");

            String path = "/ncs:services/" + nipap.prefix + ":" + nipap.prefix + "/" +
              nipap._from_pool_ + req.pool_key + "/request" + req.request_key;

            ConfUInt64 p_id = (ConfUInt64)wsess.getElem(
                path +"/" +nipap._response_ + "/" + nipap._from_pool_ + "/" + nipap._prefix_id_);

            Prefix parentPrefix= Prefix.get(nipapCon, Integer.parseInt(String.valueOf(p_id)));

            addPrefixFromPrefix(path, parentPrefix, req.prefix_key);
          }
          else if (req.op == Operation.DEALLOCATE &&
                  (req.t == Type.Request)) {
              //Deallocate prefix

              String path = req.path + "/" + nipap._response_ + "/" + nipap._from_prefix_;
              int n = wsess.getNumberOfInstances(path);
              try {
                List<ConfObject[]> objArrList = wsess.getObjects(4, 0, n, path);
                for ( int i = 0; i < objArrList.size(); i++){
                  ConfObject[] objArr = objArrList.get(i);
                  LOGGER.info(objArr[0]);
                  ConfKey t = new ConfKey(objArr[0]);
                  removeChildPrefix(req.path+ "/" + nipap._response_ + "/" + nipap._from_prefix_ + t);
                }
              }catch (Exception e){
              }

              removePrefix(req.path + "/" + nipap._response_ + "/" + nipap._from_pool_);
              removeResponse(req.path + "/" + nipap._response_ + "/" + nipap._from_pool_);
            }
          }
            // Tell the subscription we are done 
            sub.sync(CdbSubscriptionSyncType.DONE_PRIORITY);
          }
        }
        catch (SocketException e) {
            // silence here, normal close (redeploy/reload package)
        }
        catch (Exception e) {
            LOGGER.error("",e );
        }
    }

    public void finish() {
        safeclose(cdb);
        safeclose(wcdb);
        try {
            maapi.getSocket().close();
        }
        catch (Exception e) {
        }
    }


    private void safeclose(Cdb s) {
        try {s.close();}
        catch (Exception ignore) {}
    }


    private enum Operation { ALLOCATE, DEALLOCATE }
    private enum Type { Request, FromPrefixRequest, Prefix }

    private class Request {
        Operation op;
        Type t;
        ConfPath path;
        ConfKey pool_key;
        ConfKey request_key;
        ConfKey prefix_key;
    }

    private class Iter implements CdbDiffIterate {
        CdbSubscription cdbSub;

        Iter(CdbSubscription sub ) {
            this.cdbSub = sub;
        }

        public DiffIterateResultFlag iterate(
                ConfObject[] kp,
                DiffIterateOperFlag op,
                ConfObject oldValue,
                ConfObject newValue, Object initstate) {     

            @SuppressWarnings("unchecked")
            ArrayList<Request> reqs = (ArrayList<Request>) initstate;

            try {
                ConfPath p = new ConfPath(kp);
                LOGGER.info("ITER " + op + " " + p);
                LOGGER.info("length " + kp.length);
                Request r = new Request();
                r.path = p;


                switch(op) {

                  case MOP_CREATED: {
                    // new request
                    if(kp[1].toString().equals("nipap:request") && 
                        kp.length == 6){
                      r.pool_key = (ConfKey)kp[2];
                      r.request_key = (ConfKey)kp[0];
                      r.t = Type.Request;
                      r.op = Operation.ALLOCATE;
                      reqs.add(r);
                      //the request is new, we dont need to look at children
                      return DiffIterateResultFlag.ITER_CONTINUE;
                    }
                    else if(kp[1].toString().equals("nipap:from-prefix-request") && 
                        kp.length == 8){
                      r.prefix_key = (ConfKey)kp[0];
                      r.request_key = (ConfKey)kp[2];
                      r.pool_key = (ConfKey)kp[4];
                      r.t = Type.FromPrefixRequest;
                      r.op = Operation.ALLOCATE;
                      reqs.add(r);
                      //the request is new, we dont need to look at children
                      return DiffIterateResultFlag.ITER_CONTINUE;
                    }
                    
                    break;
                  }
                  case MOP_DELETED: {
                    if(kp[1].toString().equals("nipap:request") && 
                        kp.length == 6){
                      r.pool_key = (ConfKey)kp[2];
                      r.request_key = (ConfKey)kp[0];
                      r.t = Type.Request;
                      r.op = Operation.DEALLOCATE;
                      reqs.add(r);
                      //we dont need to look at children
                      return DiffIterateResultFlag.ITER_CONTINUE;
                    }
                    break;
                  }
              }
            }
            catch (Exception e) {
                LOGGER.error("", e);
            }
            return DiffIterateResultFlag.ITER_RECURSE;

        } 
    }

    // redeploy MUST be done in another thread, if not system
    // hangs, since the CDB subscriber cannot do its work
    private void redeploy(String path) {
        Redeployer r = new Redeployer(path);
        Thread t = new Thread(r);
        t.start();
    }

    private class Redeployer implements Runnable {
        private String path;
        private ConfKey k;
        private Maapi m;
        private Socket s;

        public Redeployer(String path) {
            this.path = path; this.k = k;

            try {
                s = new Socket(NcsMain.getInstance().getNcsHost(),
                               NcsMain.getInstance().getNcsPort());
                m = new Maapi(s);

                m.startUserSession("admin",
                                   m.getSocket().getInetAddress(),
                                   "system",
                                   new String[] {"admin"},
                                   MaapiUserSessionFlag.PROTO_TCP);
            } catch (Exception e) {
                System.err.println("redeployer exception: "+e);
            }

        }

        public void run() {
            try {
                // must be different, we want to redeploy owner if
                // he exists
                int tid = m.startTrans(Conf.DB_RUNNING, Conf.MODE_READ);
                System.err.println("invoking redeploy on "+path);

                int counter = 0;
                while (true) {
                  Thread.sleep(50);
                  if (m.exists(tid, path))
                    break;
                  if (counter++ == 40) {
                    break;
                  }
                  Thread.sleep(1000);
                }

                m.requestAction(new ConfXMLParam[] {},
                                path+"/reactive-re-deploy");
                try {
                    m.finishTrans(tid);
                }
                catch (Throwable ignore) {
                }
                s.close();
            } catch (Exception e) {
                LOGGER.error("error in reactive-re-deploy: "+path, e);
                return;
            }
        }
    }
}
