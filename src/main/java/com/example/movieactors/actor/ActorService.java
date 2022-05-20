package com.example.movieactors.actor;

import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class ActorService {

    private final ActorsDao actorsDao;

    public ActorService(ActorsDao actorsDao) {
        this.actorsDao = actorsDao;
    }

    public List<Actor> getActors(){
        return actorsDao.selectActors();
    }

    public void addNewActor(Actor actor) {
        int result = actorsDao.insertActor(actor);
        if (result!=1) {
            throw new IllegalStateException("something went wrong");
        }
    }

}
